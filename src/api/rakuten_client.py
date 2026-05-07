"""楽天市場商品検索APIのラッパークライアント。

楽天ウェブサービス利用規約に基づき、取得データは集計・統計値のみに使用する。
商品個別データの再配布・個別表示は行わない。
"""

import json
import sqlite3
import time
from pathlib import Path
from typing import Any

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from config.settings import (
    RAKUTEN_ACCESS_KEY,
    RAKUTEN_APP_ID,
    RAKUTEN_ITEM_SEARCH_URL,
    RAKUTEN_MAX_HITS_PER_PAGE,
    SQLITE_CACHE_PATH,
)
from src.utils.logger import logger
from src.utils.rate_limiter import RateLimiter


class RakutenClient:
    """楽天市場商品検索APIクライアント。

    - SQLite キャッシュで同一リクエストの再取得を防ぐ
    - RateLimiter で 1req/sec を厳守
    - tenacity で一時的なエラー時に自動リトライ

    Example:
        client = RakutenClient()
        items = client.search_items(keyword="ふるさと納税 牛肉", page=1)
    """

    def __init__(self, cache_path: Path = SQLITE_CACHE_PATH) -> None:
        """初期化。

        Args:
            cache_path: SQLite キャッシュファイルのパス。
        """
        if not RAKUTEN_APP_ID:
            raise ValueError(
                "RAKUTEN_APP_ID が設定されていません。.env ファイルを確認してください。"
            )
        if not RAKUTEN_ACCESS_KEY:
            raise ValueError(
                "RAKUTEN_ACCESS_KEY が設定されていません。.env ファイルを確認してください。"
            )

        self._app_id = RAKUTEN_APP_ID
        self._access_key = RAKUTEN_ACCESS_KEY
        self._rate_limiter = RateLimiter(requests_per_second=1.0)
        self._session = requests.Session()
        # 新APIエンドポイントはReferer/Originヘッダーが必須
        self._session.headers.update({
            "Referer": "https://tetsun-0320.github.io/furusato-nozei-trends/",
            "Origin": "https://tetsun-0320.github.io",
        })
        self._cache_conn = self._init_cache(cache_path)

    def _init_cache(self, cache_path: Path) -> sqlite3.Connection:
        """SQLite キャッシュを初期化する。"""
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(cache_path)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS api_cache (
                cache_key TEXT PRIMARY KEY,
                response_json TEXT NOT NULL,
                fetched_at REAL NOT NULL
            )
            """
        )
        conn.commit()
        return conn

    def _get_cache(self, cache_key: str) -> dict[str, Any] | None:
        """キャッシュからレスポンスを取得する。"""
        row = self._cache_conn.execute(
            "SELECT response_json FROM api_cache WHERE cache_key = ?",
            (cache_key,),
        ).fetchone()
        if row:
            return json.loads(row[0])
        return None

    def _set_cache(self, cache_key: str, response: dict[str, Any]) -> None:
        """レスポンスをキャッシュに保存する。"""
        self._cache_conn.execute(
            "INSERT OR REPLACE INTO api_cache (cache_key, response_json, fetched_at) VALUES (?, ?, ?)",
            (cache_key, json.dumps(response, ensure_ascii=False), time.time()),
        )
        self._cache_conn.commit()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def _fetch(self, params: dict[str, Any]) -> dict[str, Any]:
        """APIリクエストを実行する（リトライ付き）。"""
        self._rate_limiter.wait()
        response = self._session.get(
            RAKUTEN_ITEM_SEARCH_URL,
            params=params,
            timeout=10,
        )
        if not response.ok:
            logger.error(f"APIエラー {response.status_code}: {response.text}")
        response.raise_for_status()
        return response.json()

    def search_items(
        self,
        keyword: str,
        page: int = 1,
        genre_id: str | None = None,
        hits: int = RAKUTEN_MAX_HITS_PER_PAGE,
        use_cache: bool = True,
    ) -> dict[str, Any]:
        """商品を検索し、レスポンス全体を返す。

        Args:
            keyword: 検索キーワード（例: "ふるさと納税 牛肉"）。
            page: ページ番号（1始まり）。
            genre_id: 楽天ジャンルID。指定するとジャンル絞り込みが可能。
            hits: 1ページあたりの取得件数（最大30）。
            use_cache: True の場合、キャッシュがあればAPIを叩かない。

        Returns:
            楽天API のレスポンス dict。
        """
        params: dict[str, Any] = {
            "applicationId": self._app_id,
            "accessKey": self._access_key,
            "keyword": keyword,
            "page": page,
            "hits": hits,
            "sort": "-reviewCount",  # レビュー数降順で人気商品を優先
            "format": "json",
        }
        if genre_id:
            params["genreId"] = genre_id

        # キャッシュキーはパラメータのソート済み文字列で生成
        cache_key = "&".join(f"{k}={v}" for k, v in sorted(params.items()))

        if use_cache:
            cached = self._get_cache(cache_key)
            if cached:
                logger.debug(f"キャッシュヒット: {keyword} page={page}")
                return cached

        logger.info(f"APIリクエスト: {keyword} page={page}")
        response = self._fetch(params)
        self._set_cache(cache_key, response)
        return response

    def get_total_pages(
        self, keyword: str, genre_id: str | None = None
    ) -> int:
        """指定キーワードの総ページ数を取得する。

        Args:
            keyword: 検索キーワード。
            genre_id: 楽天ジャンルID。

        Returns:
            総ページ数（楽天APIの上限は100ページ）。
        """
        response = self.search_items(keyword=keyword, page=1, genre_id=genre_id)
        total_pages = response.get("pageCount", 1)
        # 楽天APIの上限は100ページ
        return min(total_pages, 100)

    def close(self) -> None:
        """リソースを解放する。"""
        self._cache_conn.close()
        self._session.close()

    def __enter__(self) -> "RakutenClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
