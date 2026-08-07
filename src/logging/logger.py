"""Application Logger — standard python logging with rotation."""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from config.constants import LOG_LEVEL


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        # Console handler
        console = logging.StreamHandler()
        console.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
        ))
        logger.addHandler(console)

        # Ensure logs directory exists
        Path("logs").mkdir(parents=True, exist_ok=True)

        # File handler with rotation (max 5MB, keep 3 backups)
        file_handler = RotatingFileHandler(
            "logs/crypto_prime.log",
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
        )
        file_handler.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
        ))
        logger.addHandler(file_handler)

        logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

    return logger