"""カテゴリ別分析モジュール。

カテゴリ別の人気構造・価格帯・レビュー評価を集計する。
"""

import pandas as pd
import numpy as np


def category_summary(df: pd.DataFrame) -> pd.DataFrame:
    """カテゴリ別の主要指標を集計する。

    Args:
        df: 'category', 'item_price', 'review_count', 'review_average' 列を持つ DataFrame。

    Returns:
        カテゴリ別集計 DataFrame。
    """
    agg = df.groupby("category").agg(
        件数=("item_price", "count"),
        価格_中央値=("item_price", "median"),
        価格_平均=("item_price", "mean"),
        価格_最小=("item_price", "min"),
        価格_最大=("item_price", "max"),
        レビュー数_合計=("review_count", "sum"),
        レビュー数_中央値=("review_count", "median"),
        レビュー数_平均=("review_count", "mean"),
    ).reset_index()

    # レビューあり商品の評価平均（review_average=0 は未評価として除外）
    rating_avg = (
        df[df["review_average"] > 0]
        .groupby("category")["review_average"]
        .mean()
        .reset_index()
        .rename(columns={"review_average": "評価平均"})
    )
    agg = agg.merge(rating_avg, on="category", how="left")

    # 構成比
    agg["構成比"] = agg["件数"] / agg["件数"].sum() * 100

    return agg.sort_values("件数", ascending=False).reset_index(drop=True)


def category_price_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """カテゴリ × 価格帯のクロス集計。

    Args:
        df: 'category', 'item_price' 列を持つ DataFrame。

    Returns:
        カテゴリ × 価格帯の件数クロス表。
    """
    bins = [0, 5_000, 10_000, 20_000, 30_000, 50_000, 100_000, float("inf")]
    labels = ["〜5千", "5千〜1万", "1〜2万", "2〜3万", "3〜5万", "5〜10万", "10万〜"]
    df = df.copy()
    df["価格帯"] = pd.cut(df["item_price"], bins=bins, labels=labels)
    cross = pd.crosstab(df["category"], df["価格帯"], normalize="index") * 100
    return cross.round(1)


def category_shop_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """カテゴリ × 自治体（ショップ）別の集計。

    同じカテゴリ内でも自治体によって価格・レビューに差があるかを確認する。

    Args:
        df: 'category', 'shop_name', 'item_price', 'review_count', 'review_average' 列を持つ DataFrame。

    Returns:
        カテゴリ × 自治体別の集計 DataFrame。
    """
    agg = (
        df.groupby(["category", "shop_name"])
        .agg(
            商品数=("item_price", "count"),
            価格_中央値=("item_price", "median"),
            レビュー数_合計=("review_count", "sum"),
            評価平均=("review_average", lambda x: x[x > 0].mean()),
        )
        .reset_index()
    )
    # 各カテゴリ内でレビュー数合計の降順にランク付け
    agg["カテゴリ内レビューランク"] = (
        agg.groupby("category")["レビュー数_合計"]
        .rank(ascending=False, method="min")
        .astype(int)
    )
    return agg.sort_values(["category", "カテゴリ内レビューランク"])
