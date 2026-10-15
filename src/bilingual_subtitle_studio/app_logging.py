"""Set up local troubleshooting logs written to logs/app.log."""

from __future__ import annotations

import logging
from pathlib import Path

LOG_PATH = Path("logs/app.log")


def get_logger(name: str = "bilingual_subtitle_studio") -> logging.Logger:
    """Return a named logger that writes to the local log file.

    Handlers are attached once per logger, so calling this repeatedly is safe.

    Args:
        name: Logger name, usually the module that logs.

    Returns:
        The configured logger.
    """
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if not any(isinstance(handler, logging.FileHandler) for handler in logger.handlers):
        handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
        handler.setFormatter(
            logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
        )
        logger.addHandler(handler)

    return logger
