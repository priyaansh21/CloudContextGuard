"""
Application logging for CloudContextGuard.

Logs are written under the project's portable ``logs/`` directory
(``app.core.paths.LOG_DIR``), never to a hardcoded location. Never log
secrets, passwords, tokens or credentials.
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from app.core.paths import LOG_DIR, ensure_directories

LOG_FILE = LOG_DIR / "cloudcontextguard.log"
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

_configured = False


def configure_logging(level: int = logging.INFO) -> logging.Logger:
    """Configure root logging once and return the application logger."""
    global _configured

    logger = logging.getLogger("cloudcontextguard")

    if _configured:
        return logger

    ensure_directories()

    formatter = logging.Formatter(LOG_FORMAT)

    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=1_000_000, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.setLevel(level)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.propagate = False

    _configured = True
    return logger


def get_logger() -> logging.Logger:
    """Return the application logger, configuring it on first use."""
    return configure_logging()
