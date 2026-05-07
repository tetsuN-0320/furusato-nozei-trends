"""楽天APIのレート制限対応モジュール。1リクエスト/秒を厳守する。"""

import time
from threading import Lock


class RateLimiter:
    """スレッドセーフなレート制限器。

    楽天ウェブサービスの利用規約に定められた
    1リクエスト/秒 の制限を守るために使用する。

    Example:
        limiter = RateLimiter(requests_per_second=1.0)
        for page in range(total_pages):
            limiter.wait()  # 必要な場合だけ待機
            response = requests.get(url)
    """

    def __init__(self, requests_per_second: float = 1.0) -> None:
        """初期化。

        Args:
            requests_per_second: 1秒あたりの最大リクエスト数。デフォルト1.0。
        """
        self._min_interval = 1.0 / requests_per_second
        self._last_called: float = 0.0
        self._lock = Lock()

    def wait(self) -> None:
        """前回のリクエストから最小インターバルが経過するまで待機する。

        スレッドセーフ。複数スレッドから呼んでも安全。
        """
        with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_called
            remaining = self._min_interval - elapsed
            if remaining > 0:
                time.sleep(remaining)
            self._last_called = time.monotonic()
