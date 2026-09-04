"""Binance-specific exceptions."""

from src.core.types.enums import ExchangeErrorType


class BinanceAPIError(Exception):
    def __init__(self, message: str, error_type: ExchangeErrorType = ExchangeErrorType.UNKNOWN):
        super().__init__(message)
        self.error_type = error_type
