"""自治体タイプ分類モジュール。

楽天データと総務省データを突合し、K-meansで自治体を戦略タイプに分類する。
"""

import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


# クラスタリングに使う特徴量
FEATURE_COLS = [
    "商品数",
    "価格_中央値",
    "レビュー数_合計",
    "評価平均",
    "食品比率",        # 食品カテゴリ（肉・魚・果物・野菜・米）の商品比率
    "高額品比率",      # 3万円以上の商品比率
    "受入額_億円",     # 総務省データ（令和4年度）
]

FOOD_CATEGORIES = {"牛肉", "豚肉", "鶏肉", "魚介類", "果物", "野菜", "米・穀物", "加工食品・惣菜", "スイーツ・菓子"}


def build_shop_features(df_rakuten: pd.DataFrame) -> pd.DataFrame:
    """楽天データからショップ（自治体）別特徴量を作成する。

    Args:
        df_rakuten: 'shop_name', 'category', 'item_price', 'review_count', 'review_average' 列を持つ DataFrame。

    Returns:
        ショップ別特徴量 DataFrame。
    """
    agg = df_rakuten.groupby("shop_name").agg(
        商品数=("item_price", "count"),
        価格_中央値=("item_price", "median"),
        価格_平均=("item_price", "mean"),
        レビュー数_合計=("review_count", "sum"),
        レビュー数_平均=("review_count", "mean"),
        評価平均=("review_average", lambda x: x[x > 0].mean()),
    ).reset_index()

    # 食品比率
    food_counts = (
        df_rakuten[df_rakuten["category"].isin(FOOD_CATEGORIES)]
        .groupby("shop_name")
        .size()
        .reset_index(name="食品数")
    )
    agg = agg.merge(food_counts, on="shop_name", how="left")
    agg["食品数"] = agg["食品数"].fillna(0)
    agg["食品比率"] = agg["食品数"] / agg["商品数"]

    # 高額品比率（3万円以上）
    high_counts = (
        df_rakuten[df_rakuten["item_price"] >= 30_000]
        .groupby("shop_name")
        .size()
        .reset_index(name="高額品数")
    )
    agg = agg.merge(high_counts, on="shop_name", how="left")
    agg["高額品数"] = agg["高額品数"].fillna(0)
    agg["高額品比率"] = agg["高額品数"] / agg["商品数"]

    # 主力カテゴリ（最多カテゴリ）
    dominant = (
        df_rakuten.groupby(["shop_name", "category"])
        .size()
        .reset_index(name="n")
        .sort_values("n", ascending=False)
        .drop_duplicates("shop_name")
        .rename(columns={"category": "主力カテゴリ"})
        [["shop_name", "主力カテゴリ"]]
    )
    agg = agg.merge(dominant, on="shop_name", how="left")

    return agg


def merge_soumu(df_shops: pd.DataFrame, df_soumu: pd.DataFrame) -> pd.DataFrame:
    """楽天ショップ特徴量と総務省データを突合する。

    shop_name（例: 「北海道別海町」）と総務省の「都道府県名+市区町村名」で
    部分一致マッチングを行う。

    Args:
        df_shops: build_shop_features() の出力。
        df_soumu: load_soumu_csv() の出力。

    Returns:
        突合済み DataFrame。突合できなかった行は受入額=0。
    """
    # 総務省側: 都道府県+市区町村の結合キーを作成
    df_soumu = df_soumu.copy()
    df_soumu["自治体フル"] = df_soumu["都道府県名"] + df_soumu["市区町村名"]
    df_soumu["受入額_億円"] = df_soumu["受入額_合計"] / 100_000

    # 楽天 shop_name から都道府県プレフィックスを除いた市区町村名を抽出
    # shop_name の例: "北海道別海町", "岩手県花巻市", "大阪府大阪市"
    matched_rows = []
    for _, shop_row in df_shops.iterrows():
        shop = shop_row["shop_name"]
        # 総務省側で shop_name を含む行を探す
        mask = df_soumu["自治体フル"].str.contains(shop, regex=False, na=False)
        if mask.any():
            soumu_row = df_soumu[mask].iloc[0]
            matched_rows.append({
                "shop_name": shop,
                "都道府県名": soumu_row["都道府県名"],
                "市区町村名": soumu_row["市区町村名"],
                "受入額_億円": soumu_row["受入額_億円"],
                "受入件数": soumu_row["受入件数"],
            })
        else:
            matched_rows.append({
                "shop_name": shop,
                "都道府県名": None,
                "市区町村名": None,
                "受入額_億円": 0.0,
                "受入件数": 0,
            })

    df_match = pd.DataFrame(matched_rows)
    result = df_shops.merge(df_match, on="shop_name", how="left")
    match_rate = result["都道府県名"].notna().mean() * 100
    return result, match_rate


def run_kmeans(df: pd.DataFrame, n_clusters: int = 5, random_state: int = 42) -> pd.DataFrame:
    """K-meansで自治体を戦略タイプに分類する。

    Args:
        df: build_shop_features() + merge_soumu() の出力。
        n_clusters: クラスタ数（デフォルト5）。
        random_state: 再現性のためのシード。

    Returns:
        'cluster' 列が追加された DataFrame。
    """
    feature_cols = [c for c in FEATURE_COLS if c in df.columns]
    X = df[feature_cols].fillna(0).values

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    km = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
    df = df.copy()
    df["cluster"] = km.fit_predict(X_scaled)

    return df, km, scaler


def label_clusters(df: pd.DataFrame) -> pd.DataFrame:
    """クラスタの特徴から人間が読めるラベルを付与する。

    各クラスタの特徴量平均を見て、自動的にラベルを推定する。
    （実際にはノートブックで確認しながら手動調整を推奨）

    Args:
        df: 'cluster' 列を持つ DataFrame。

    Returns:
        'cluster_label' 列が追加された DataFrame。
    """
    cluster_means = df.groupby("cluster")[
        ["価格_中央値", "食品比率", "高額品比率", "レビュー数_合計", "受入額_億円"]
    ].mean()

    labels = {}
    for c, row in cluster_means.iterrows():
        if row["高額品比率"] > 0.3 and row["食品比率"] < 0.4:
            labels[c] = "家電・高額品特化型"
        elif row["食品比率"] > 0.7 and row["価格_中央値"] < 20_000:
            labels[c] = "食品コスパ型"
        elif row["食品比率"] > 0.5 and row["価格_中央値"] >= 20_000:
            labels[c] = "食品プレミアム型"
        elif row["受入額_億円"] > cluster_means["受入額_億円"].median() * 2:
            labels[c] = "大規模総合型"
        else:
            labels[c] = "汎用・小規模型"

    df = df.copy()
    df["cluster_label"] = df["cluster"].map(labels)
    return df, labels
