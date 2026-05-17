from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def configure_logging(level: str = "INFO") -> None:
    log_level = getattr(logging, level.upper(), logging.INFO)
    log_format = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")

    Path("logs").mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(
        "logs/bot.log",
        maxBytes=2_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(log_format)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(log_format)

    logging.basicConfig(level=log_level, handlers=[stream_handler, file_handler])
