"""ロガー設定モジュール。loguru を使用してプロジェクト全体のログを統一管理する。"""

import sys

from loguru import logger

from config.settings import LOG_LEVEL


def setup_logger() -> None:
    """ロガーを初期化する。main エントリポイントで一度だけ呼ぶ。"""
    logger.remove()  # デフォルトハンドラを削除
    logger.add(
        sys.stderr,
        level=LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True,
    )
    logger.add(
        "logs/app.log",
        level="DEBUG",
        rotation="10 MB",
        retention="7 days",
        encoding="utf-8",
    )


# モジュール import 時に自動設定（notebooks からの利用を想定）
setup_logger()

__all__ = ["logger"]
