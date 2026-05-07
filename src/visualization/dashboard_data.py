"""ダッシュボード用JSON生成モジュール。

分析済みparquetファイルを読み込み、フロントエンドが直接fetchできるJSONを書き出す。
楽天規約に従い、集計・統計値のみを公開する（個別商品情報は含まない）。
"""

import json
from pathlib import Path

import pandas as pd
import numpy as np

from config.settings import ANALYSIS_DIR, PROCESSED_DIR, WEB_DATA_DIR


def _to_serializable(obj):
    """numpy/pandas 型を JSON シリアライズ可能な Python 型に変換する。"""
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return None if np.isnan(obj) else float(obj)
    if isinstance(obj, (np.ndarray,)):
        return obj.tolist()
    if isinstance(obj, pd.Categorical):
        return str(obj)
    return obj


def _write_json(data: dict | list, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=_to_serializable)


def build_summary_json(df_products: pd.DataFrame, df_cat: pd.DataFrame, df_muni: pd.DataFrame) -> dict:
    """サイト全体の KPI サマリー JSON を生成する。"""
    return {
        "total_products": int(len(df_products)),
        "total_municipalities": int(df_muni["shop_name"].nunique()),
        "total_categories": int(df_cat["category"].nunique()),
        "avg_review_score": round(float(df_products[df_products["review_average"] > 0]["review_average"].mean()), 2),
        "median_price": int(df_products["item_price"].median()),
        "top_category": str(df_cat.iloc[0]["category"]),
        "top_category_count": int(df_cat.iloc[0]["件数"]),
    }


def build_categories_json(df_cat: pd.DataFrame) -> list[dict]:
    """カテゴリ別統計 JSON を生成する。"""
    records = []
    for _, row in df_cat.iterrows():
        records.append({
            "category": str(row["category"]),
            "count": int(row["件数"]),
            "share_pct": round(float(row["構成比"]), 1),
            "median_price": int(row["価格_中央値"]),
            "avg_price": int(row["価格_平均"]),
            "total_reviews": int(row["レビュー数_合計"]),
            "median_reviews": float(row["レビュー数_中央値"]),
            "avg_rating": round(float(row["評価平均"]), 2) if pd.notna(row["評価平均"]) else None,
        })
    return records


def build_price_segments_json(df_price: pd.DataFrame) -> list[dict]:
    """価格帯別統計 JSON を生成する。"""
    records = []
    for _, row in df_price.iterrows():
        records.append({
            "segment": str(row["価格帯"]),
            "count": int(row["件数"]),
            "share_pct": round(float(row["構成比"]), 1),
            "median_reviews": float(row["レビュー数_中央値"]),
            "total_reviews": int(row["レビュー数_合計"]),
            "avg_rating": round(float(row["評価平均"]), 2) if pd.notna(row.get("評価平均")) else None,
        })
    return records


def build_municipalities_json(df_muni: pd.DataFrame) -> list[dict]:
    """自治体別統計 JSON を生成する。クラスターラベルを含む。"""
    records = []
    for _, row in df_muni.iterrows():
        records.append({
            "shop_name": str(row["shop_name"]),
            "prefecture": str(row["都道府県名"]) if pd.notna(row.get("都道府県名")) else None,
            "municipality": str(row["市区町村名"]) if pd.notna(row.get("市区町村名")) else None,
            "product_count": int(row["商品数"]),
            "median_price": int(row["価格_中央値"]),
            "total_reviews": int(row["レビュー数_合計"]),
            "avg_rating": round(float(row["評価平均"]), 2) if pd.notna(row.get("評価平均")) else None,
            "food_ratio": round(float(row["食品比率"]), 3),
            "high_price_ratio": round(float(row["高額品比率"]), 3),
            "main_category": str(row["主力カテゴリ"]) if pd.notna(row.get("主力カテゴリ")) else None,
            "donation_amount_oku": round(float(row["受入額_億円"]), 2) if pd.notna(row.get("受入額_億円")) else 0.0,
            "cluster": int(row["cluster"]) if pd.notna(row.get("cluster")) else -1,
            "cluster_label": str(row["cluster_label"]) if pd.notna(row.get("cluster_label")) else "不明",
        })
    return records


def build_scatter_json(df_products: pd.DataFrame) -> list[dict]:
    """価格×レビュー数の散布図用データ（カテゴリ別サンプリング）を生成する。

    全件だと重すぎるため、カテゴリ別に最大200件をサンプリングする。
    """
    reviewed = df_products[df_products["review_count"] > 0]
    sampled = (
        pd.concat(
            [g.nlargest(200, "review_count") for _, g in reviewed.groupby("category")]
        )
        .reset_index(drop=True)
    )

    records = []
    for _, row in sampled.iterrows():
        records.append({
            "category": str(row["category"]),
            "price": int(row["item_price"]),
            "reviews": int(row["review_count"]),
            "rating": float(row["review_average"]) if row["review_average"] > 0 else None,
        })
    return records


def generate_all(output_dir: Path | None = None) -> None:
    """全JSONファイルを生成して web/static/data/ に書き出す。"""
    out = output_dir or WEB_DATA_DIR
    out.mkdir(parents=True, exist_ok=True)

    df_products = pd.read_parquet(PROCESSED_DIR / "products.parquet")
    df_cat = pd.read_parquet(ANALYSIS_DIR / "category_stats.parquet")
    df_price = pd.read_parquet(ANALYSIS_DIR / "price_segments.parquet")
    df_muni = pd.read_parquet(ANALYSIS_DIR / "municipality_stats.parquet")

    _write_json(build_summary_json(df_products, df_cat, df_muni), out / "summary.json")
    _write_json(build_categories_json(df_cat), out / "categories.json")
    _write_json(build_price_segments_json(df_price), out / "price_segments.json")
    _write_json(build_municipalities_json(df_muni), out / "municipalities.json")
    _write_json(build_scatter_json(df_products), out / "scatter.json")
