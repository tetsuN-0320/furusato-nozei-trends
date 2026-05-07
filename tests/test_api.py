"""楽天APIクライアントのユニットテスト。

実際のAPIアクセスは `pytest -m integration` で実行。
通常のテストはモックを使用。
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# テスト用のダミーAPP_ID を設定
@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    monkeypatch.setenv("RAKUTEN_APP_ID", "test_app_id")


@pytest.fixture
def tmp_cache(tmp_path: Path):
    return tmp_path / "test_cache.sqlite"


@pytest.fixture
def sample_response():
    """楽天APIの典型的なレスポンス例。"""
    return {
        "count": 2,
        "page": 1,
        "pageCount": 10,
        "Items": [
            {
                "Item": {
                    "itemCode": "abc:123",
                    "genreId": "100227",
                    "itemName": "【ふるさと納税】A5ランク 黒毛和牛 1kg",
                    "itemPrice": 10000,
                    "reviewCount": 150,
                    "reviewAverage": 4.5,
                    "shopName": "○○市",
                    "itemCaption": "最高級の黒毛和牛をお届けします。",
                }
            },
            {
                "Item": {
                    "itemCode": "def:456",
                    "genreId": "100227",
                    "itemName": "【ふるさと納税】新鮮ホタテ 2kg",
                    "itemPrice": 15000,
                    "reviewCount": 80,
                    "reviewAverage": 4.2,
                    "shopName": "△△町",
                    "itemCaption": "北海道産のホタテを産地直送でお届け。",
                }
            },
        ],
    }


class TestRakutenClient:
    def test_init_requires_app_id(self, tmp_cache, monkeypatch):
        """APP_ID未設定時にValueErrorが発生すること。"""
        monkeypatch.setenv("RAKUTEN_APP_ID", "")
        # settings モジュールを再ロードして環境変数を反映
        import importlib

        import config.settings as settings
        importlib.reload(settings)

        from src.api.rakuten_client import RakutenClient
        with pytest.raises(ValueError, match="RAKUTEN_APP_ID"):
            RakutenClient(cache_path=tmp_cache)

    def test_search_uses_cache_on_second_call(self, tmp_cache, sample_response):
        """2回目の同一リクエストはキャッシュを使い、APIを叩かないこと。"""
        from src.api.rakuten_client import RakutenClient

        with patch("src.api.rakuten_client.requests.Session") as MockSession:
            mock_get = MockSession.return_value.get
            mock_get.return_value.json.return_value = sample_response
            mock_get.return_value.raise_for_status = MagicMock()

            client = RakutenClient(cache_path=tmp_cache)

            # 1回目: APIを叩く
            result1 = client.search_items(keyword="ふるさと納税 牛肉", page=1)
            assert mock_get.call_count == 1

            # 2回目: キャッシュから取得（API呼び出しなし）
            result2 = client.search_items(keyword="ふるさと納税 牛肉", page=1)
            assert mock_get.call_count == 1  # 増えていない

            assert result1 == result2
            client.close()

    def test_get_total_pages_capped_at_100(self, tmp_cache, sample_response):
        """総ページ数が100を超える場合は100に制限されること。"""
        from src.api.rakuten_client import RakutenClient

        large_response = {**sample_response, "pageCount": 500}

        with patch("src.api.rakuten_client.requests.Session") as MockSession:
            mock_get = MockSession.return_value.get
            mock_get.return_value.json.return_value = large_response
            mock_get.return_value.raise_for_status = MagicMock()

            client = RakutenClient(cache_path=tmp_cache)
            pages = client.get_total_pages("ふるさと納税")
            assert pages == 100
            client.close()


@pytest.mark.integration
class TestRakutenClientIntegration:
    """実際のAPIに接続する統合テスト。`pytest -m integration` で実行。"""

    def test_real_search(self):
        """実際のAPIで1件以上の商品が取得できること。"""
        from src.api.rakuten_client import RakutenClient

        with RakutenClient() as client:
            response = client.search_items(keyword="ふるさと納税 牛肉", page=1)
            assert response.get("count", 0) > 0
