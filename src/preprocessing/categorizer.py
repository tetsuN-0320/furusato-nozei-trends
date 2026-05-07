"""カテゴリ正規化モジュール。

商品名（item_name）をキーワードマッチングで主要カテゴリに分類する。
ルールは config/category_mapping.yml で管理し、コードを汚さない。
"""

import re
from pathlib import Path

import pandas as pd
import yaml

from config.settings import CATEGORY_MAPPING_PATH
from src.utils.logger import logger


class Categorizer:
    """商品名を主要カテゴリに正規化するクラス。

    YAMLのキーワードリストを使い、商品名に含まれるキーワードで
    カテゴリを決定する。複数マッチした場合は priority 順で決定。

    Example:
        cat = Categorizer()
        category = cat.classify("【ふるさと納税】A5黒毛和牛 1kg")
        # → "牛肉"
    """

    def __init__(self, mapping_path: Path = CATEGORY_MAPPING_PATH) -> None:
        """初期化。YAMLを読み込んでパターンを構築する。"""
        with open(mapping_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)

        self._categories: dict[str, list[str]] = {
            name: data.get("keywords", []) or []
            for name, data in config["categories"].items()
        }
        self._priority: list[str] = config.get("priority", list(self._categories.keys()))

        # カテゴリごとにキーワードを結合した正規表現パターンを事前コンパイル
        self._patterns: dict[str, re.Pattern] = {}
        for cat, keywords in self._categories.items():
            if keywords:
                pattern = "|".join(re.escape(kw) for kw in keywords)
                self._patterns[cat] = re.compile(pattern)

        logger.debug(f"Categorizer 初期化完了: {len(self._categories)} カテゴリ")

    def classify(self, item_name: str) -> str:
        """商品名からカテゴリを1つ返す。

        Args:
            item_name: 楽天の商品名文字列。

        Returns:
            カテゴリ名（マッチなしの場合は "その他"）。
        """
        for cat in self._priority:
            pattern = self._patterns.get(cat)
            if pattern and pattern.search(item_name):
                return cat
        return "その他"

    def classify_series(self, series: pd.Series) -> pd.Series:
        """pandas Series に対して一括分類する。

        Args:
            series: 商品名の Series。

        Returns:
            カテゴリ名の Series（同じインデックス）。
        """
        return series.apply(self.classify)


def add_category(df: pd.DataFrame) -> pd.DataFrame:
    """DataFrameに 'category' 列を追加して返す。

    Args:
        df: 'item_name' 列を持つ DataFrame。

    Returns:
        'category' 列が追加された DataFrame。
    """
    cat = Categorizer()
    df = df.copy()
    df["category"] = cat.classify_series(df["item_name"])

    # カテゴリ分布をログに出力
    dist = df["category"].value_counts()
    logger.info("カテゴリ分布:\n" + dist.to_string())
    coverage = (df["category"] != "その他").sum() / len(df) * 100
    logger.info(f"カテゴリ付与率: {coverage:.1f}%")

    return df
