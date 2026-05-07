"""プロジェクト設定。環境変数と定数を一元管理する。"""

import os
from pathlib import Path

from dotenv import load_dotenv

# プロジェクトルートからの相対パスで .env を読み込む
_PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(_PROJECT_ROOT / ".env")

# === 楽天API ===
RAKUTEN_APP_ID: str = os.environ.get("RAKUTEN_APP_ID", "")
RAKUTEN_ACCESS_KEY: str = os.environ.get("RAKUTEN_ACCESS_KEY", "")
RAKUTEN_AFFILIATE_ID: str = os.environ.get("RAKUTEN_AFFILIATE_ID", "")

# 楽天市場商品検索API エンドポイント（2026年版新エンドポイント）
RAKUTEN_ITEM_SEARCH_URL = "https://openapi.rakuten.co.jp/ichibams/api/IchibaItem/Search/20260401"

# レート制限: 1リクエスト/秒、30,000リクエスト/日
RAKUTEN_RATE_LIMIT_RPS = 1.0
RAKUTEN_MAX_DAILY_REQUESTS = 30_000

# 1リクエストで取得できる最大件数
RAKUTEN_MAX_HITS_PER_PAGE = 30

# === ふるさと納税ジャンルID ===
# 楽天市場でのふるさと納税カテゴリのジャンルID
# 参考: https://webservice.rakuten.co.jp/documentation/ichiba-genre-search
FURUSATO_GENRE_ID = "100227"  # ふるさと納税

# === ディレクトリパス ===
DATA_DIR = _PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
ANALYSIS_DIR = DATA_DIR / "analysis"
WEB_DATA_DIR = _PROJECT_ROOT / "docs" / "static" / "data"
CONFIG_DIR = _PROJECT_ROOT / "config"

# SQLite キャッシュのパス
SQLITE_CACHE_PATH = RAW_DIR / "rakuten_cache.sqlite"

# カテゴリマッピング YAML
CATEGORY_MAPPING_PATH = CONFIG_DIR / "category_mapping.yml"

# === ロギング ===
LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")
