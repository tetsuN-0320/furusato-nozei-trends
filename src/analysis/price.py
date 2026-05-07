"""価格帯戦略分析モジュール。

返礼品の価格帯分布・心理的価格設定・価格×評価の関係を分析する。
"""

import pandas as pd
import numpy as np


# 分析対象の標準価格帯ラベル
PRICE_BINS = [0, 5_000, 10_000, 20_000, 30_000, 50_000, 100_000, float("inf")]
PRICE_LABELS = ["〜5千円", "5千〜1万円", "1〜2万円", "2〜3万円", "3〜5万円", "5〜10万円", "10万円〜"]


def add_price_segment(df: pd.DataFrame) -> pd.DataFrame:
    """DataFrame に '価格帯' 列を追加する。"""
    df = df.copy()
    df["価格帯"] = pd.cut(df["item_price"], bins=PRICE_BINS, labels=PRICE_LABELS)
    return df


def price_segment_summary(df: pd.DataFrame) -> pd.DataFrame:
    """価格帯別の主要指標を集計する。

    Args:
        df: 'item_price', 'review_count', 'review_average' 列を持つ DataFrame。

    Returns:
        価格帯別集計 DataFrame。
    """
    df = add_price_segment(df)

    agg = df.groupby("価格帯", observed=True).agg(
        件数=("item_price", "count"),
        レビュー数_中央値=("review_count", "median"),
        レビュー数_合計=("review_count", "sum"),
    ).reset_index()

    rating = (
        df[df["review_average"] > 0]
        .groupby("価格帯", observed=True)["review_average"]
        .mean()
        .reset_index()
        .rename(columns={"review_average": "評価平均"})
    )
    agg = agg.merge(rating, on="価格帯", how="left")
    agg["構成比"] = agg["件数"] / agg["件数"].sum() * 100

    return agg


def popular_price_points(df: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
    """最も多く設定されている価格を返す（心理的価格の確認用）。

    Args:
        df: 'item_price' 列を持つ DataFrame。
        top_n: 上位何件を返すか。

    Returns:
        価格 × 件数の DataFrame。
    """
    counts = df["item_price"].value_counts().head(top_n).reset_index()
    counts.columns = ["価格（円）", "件数"]
    counts["累積構成比"] = counts["件数"].cumsum() / len(df) * 100
    return counts


def price_review_correlation(df: pd.DataFrame) -> pd.DataFrame:
    """価格帯別のレビュー数・評価との相関を分析する。

    Args:
        df: 'item_price', 'review_count', 'review_average' 列を持つ DataFrame。

    Returns:
        価格帯 × レビュー指標の集計 DataFrame。
    """
    df = add_price_segment(df)
    df_reviewed = df[df["review_count"] > 0]

    result = df_reviewed.groupby("価格帯", observed=True).agg(
        件数=("review_count", "count"),
        レビュー数_p25=("review_count", lambda x: x.quantile(0.25)),
        レビュー数_中央値=("review_count", "median"),
        レビュー数_p75=("review_count", lambda x: x.quantile(0.75)),
        評価平均=("review_average", "mean"),
    ).reset_index()

    return result


def category_price_positioning(df: pd.DataFrame) -> pd.DataFrame:
    """カテゴリ × 価格帯のポジショニングマップ用データを生成する。

    各カテゴリの「最頻価格帯」と「レビュー獲得力（レビュー数中央値）」を返す。
    ECのカテゴリマネジメント的な視点で使用する。

    Args:
        df: 'category', 'item_price', 'review_count' 列を持つ DataFrame。

    Returns:
        カテゴリ別のポジショニング指標 DataFrame。
    """
    df = add_price_segment(df)

    # 最頻価格帯
    dominant_segment = (
        df.groupby(["category", "価格帯"], observed=True)
        .size()
        .reset_index(name="件数")
        .sort_values("件数", ascending=False)
        .drop_duplicates("category")
        .rename(columns={"価格帯": "主力価格帯"})
        [["category", "主力価格帯"]]
    )

    agg = df.groupby("category").agg(
        商品数=("item_price", "count"),
        価格_中央値=("item_price", "median"),
        レビュー数_中央値=("review_count", "median"),
        レビュー数_合計=("review_count", "sum"),
        評価平均=("review_average", lambda x: x[x > 0].mean()),
    ).reset_index()

    return agg.merge(dominant_segment, on="category").sort_values("レビュー数_合計", ascending=False)
