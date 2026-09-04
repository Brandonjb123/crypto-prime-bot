import sys

from loguru import logger

from config.settings import settings


def setup_logger() -> None:
    """Configure loguru logger untuk seluruh aplikasi."""
    logger.remove()

    # Console output
    logger.add(
        sys.stdout,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        ),
        level=settings.LOG_LEVEL,
        colorize=True,
    )

    # File output
    logger.add(
        "logs/crypto_prime_{time:YYYY-MM-DD}.log",
        rotation="00:00",
        retention="7 days",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{line} | {message}",
    )

    logger.info("Logger initialized — Crypto Prime Bot v2.0")
