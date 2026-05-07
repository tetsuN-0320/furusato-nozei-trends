"""楽天APIからふるさと納税の返礼品データを一括取得するCLIスクリプト。

使い方:
    python scripts/fetch_data.py
    python scripts/fetch_data.py --max-pages 10   # テスト用（ページ数制限）
    python scripts/fetch_data.py --no-cache       # キャッシュを使わず再取得
"""

import argparse
import sys
from pathlib import Path

# プロジェクトルートを Python パスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd

from config.settings import FURUSATO_GENRE_ID, PROCESSED_DIR
from src.api.rakuten_client import RakutenClient
from src.utils.logger import logger

# 検索キーワード一覧（ジャンルIDと組み合わせてカバレッジを高める）
SEARCH_KEYWORDS = [
    "ふるさと納税 牛肉",
    "ふるさと納税 豚肉",
    "ふるさと納税 鶏肉",
    "ふるさと納税 魚",
    "ふるさと納税 カニ",
    "ふるさと納税 ホタテ",
    "ふるさと納税 果物",
    "ふるさと納税 野菜",
    "ふるさと納税 米",
    "ふるさと納税 酒",
    "ふるさと納税 家電",
    "ふるさと納税 旅行",
    "ふるさと納税 日用品",
]


def extract_items(response: dict) -> list[dict]:
    """APIレスポンスから商品リストを抽出する。

    Args:
        response: 楽天API のレスポンス dict。

    Returns:
        商品情報の dict リスト。集計に必要な項目のみ抽出し、
        個別商品データの保持を最小限にとどめる（規約対応）。
    """
    items = []
    for item_wrapper in response.get("Items", []):
        item = item_wrapper.get("Item", {})
        # 規約上、集計目的で必要な統計項目のみ保持する
        items.append(
            {
                "item_code": item.get("itemCode", ""),
                "genre_id": item.get("genreId", ""),
                "item_price": item.get("itemPrice", 0),
                "review_count": item.get("reviewCount", 0),
                "review_average": item.get("reviewAverage", 0.0),
                "shop_name": item.get("shopName", ""),
                "item_caption_snippet": item.get("itemCaption", "")[:200],  # 最初の200文字のみ
                "item_name": item.get("itemName", ""),
            }
        )
    return items


def fetch_all(max_pages: int | None = None, use_cache: bool = True) -> pd.DataFrame:
    """全キーワードのデータを取得してDataFrameにまとめる。

    Args:
        max_pages: 各キーワードの最大取得ページ数（None = 全ページ）。
        use_cache: True の場合、キャッシュを使用する。

    Returns:
        全商品データの DataFrame。
    """
    all_items: list[dict] = []

    with RakutenClient() as client:
        for keyword in SEARCH_KEYWORDS:
            total_pages = client.get_total_pages(keyword, genre_id=None)
            if max_pages:
                total_pages = min(total_pages, max_pages)

            logger.info(f"取得開始: '{keyword}' ({total_pages} ページ)")

            for page in range(1, total_pages + 1):
                try:
                    response = client.search_items(
                        keyword=keyword,
                        page=page,
                        genre_id=None,
                        use_cache=use_cache,
                    )
                    items = extract_items(response)
                    # キーワード列を付与（後でカテゴリ推定に使用）
                    for item in items:
                        item["search_keyword"] = keyword
                    all_items.extend(items)

                    logger.debug(f"  page {page}/{total_pages}: {len(items)} 件取得")

                except Exception as e:
                    logger.error(f"エラー: {keyword} page={page}: {e}")
                    continue

    df = pd.DataFrame(all_items)

    # 重複除去（同一 item_code が複数キーワードで引っかかる場合）
    before = len(df)
    df = df.drop_duplicates(subset=["item_code"])
    logger.info(f"重複除去: {before:,} → {len(df):,} 件")

    return df


def main() -> None:
    parser = argparse.ArgumentParser(description="楽天APIから返礼品データを取得する")
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="各キーワードの最大取得ページ数（省略時: 全ページ）",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="キャッシュを使わず再取得する",
    )
    args = parser.parse_args()

    logger.info("データ取得開始")
    df = fetch_all(max_pages=args.max_pages, use_cache=not args.no_cache)

    # 保存
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    output_path = PROCESSED_DIR / "products_raw.parquet"
    df.to_parquet(output_path, index=False)
    logger.info(f"保存完了: {output_path} ({len(df):,} 件)")


if __name__ == "__main__":
    main()
