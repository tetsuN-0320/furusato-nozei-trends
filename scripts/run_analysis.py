"""分析パイプラインを実行するCLIスクリプト。

products.parquet を読み込み、カテゴリ・価格帯・自治体の集計データを生成する。

使い方:
    python scripts/run_analysis.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd

from config.settings import ANALYSIS_DIR, PROCESSED_DIR
from src.analysis.category import category_summary
from src.analysis.municipality import build_shop_features, label_clusters, merge_soumu, run_kmeans
from src.analysis.price import price_segment_summary
from src.api.soumu_loader import load_soumu_csv
from src.utils.logger import logger


def main() -> None:
    logger.info("分析パイプライン開始")
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

    # 商品データ読み込み
    products_path = PROCESSED_DIR / "products.parquet"
    if not products_path.exists():
        logger.error(f"products.parquet が見つかりません: {products_path}")
        sys.exit(1)

    df = pd.read_parquet(products_path)
    logger.info(f"商品データ読み込み: {len(df):,} 件")

    # カテゴリ別集計
    logger.info("カテゴリ別集計...")
    cat_stats = category_summary(df)
    cat_stats.to_parquet(ANALYSIS_DIR / "category_stats.parquet", index=False)
    logger.info(f"  → {len(cat_stats)} カテゴリ")

    # 価格帯別集計
    logger.info("価格帯別集計...")
    price_stats = price_segment_summary(df)
    price_stats.to_parquet(ANALYSIS_DIR / "price_segments.parquet", index=False)
    logger.info(f"  → {len(price_stats)} 価格帯")

    # 自治体分析
    logger.info("自治体分析...")
    shop_features = build_shop_features(df)

    # 総務省データと突合
    from config.settings import RAW_DIR
    soumu_path = RAW_DIR / "soumu_donations.csv"
    if soumu_path.exists():
        df_soumu = load_soumu_csv(soumu_path)
        shop_features, match_rate = merge_soumu(shop_features, df_soumu)
        logger.info(f"  総務省データ突合率: {match_rate:.1f}%")
    else:
        shop_features["受入額_億円"] = 0.0
        shop_features["受入件数"] = 0
        shop_features["都道府県名"] = None
        shop_features["市区町村名"] = None

    # K-means クラスタリング
    shop_features, km, scaler = run_kmeans(shop_features, n_clusters=5)
    shop_features, cluster_labels = label_clusters(shop_features)
    logger.info(f"  → {len(shop_features)} 自治体をクラスタリング")
    for label, count in shop_features["cluster_label"].value_counts().items():
        logger.info(f"    {label}: {count} 自治体")

    shop_features.to_parquet(ANALYSIS_DIR / "municipality_stats.parquet", index=False)

    logger.info("分析パイプライン完了")
    logger.info(f"  出力先: {ANALYSIS_DIR}")


if __name__ == "__main__":
    main()
