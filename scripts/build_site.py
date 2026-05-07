"""フロントエンド用JSONを生成してビルドするCLIスクリプト。

使い方:
    python scripts/build_site.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import ANALYSIS_DIR, WEB_DATA_DIR
from src.utils.logger import logger
from src.visualization.dashboard_data import generate_all


def main() -> None:
    # price_segments.parquet が未生成なら run_analysis を促す
    if not (ANALYSIS_DIR / "price_segments.parquet").exists():
        logger.warning("price_segments.parquet が見つかりません。run_analysis.py を先に実行してください。")
        sys.exit(1)

    logger.info("フロントエンド用JSON生成開始")
    generate_all(output_dir=WEB_DATA_DIR)

    files = list(WEB_DATA_DIR.glob("*.json"))
    for f in files:
        size_kb = f.stat().st_size / 1024
        logger.info(f"  生成: {f.name} ({size_kb:.1f} KB)")

    logger.info(f"完了: {len(files)} ファイルを {WEB_DATA_DIR} に書き出しました")


if __name__ == "__main__":
    main()
