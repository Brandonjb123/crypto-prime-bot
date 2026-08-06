class CollectorError(Exception):
    """Base exception untuk semua collector errors."""


class DataSourceUnavailableError(CollectorError):
    """Source tidak bisa diakses (timeout, 429, dll)."""


class DataQualityError(CollectorError):
    """Data berhasil diambil tapi kualitasnya tidak cukup."""


class RateLimitError(CollectorError):
    """Rate limit tercapai."""

class InsufficientDataError(CollectorError):
    """Data tidak cukup untuk diproses (quality di bawah threshold)."""

class DuplicatePositionError(CollectorError):
    """Posisi dengan symbol dan side yang sama sudah ada."""


class PositionAlreadyClosedError(CollectorError):
    """Posisi sudah closed, tidak bisa di-close lagi."""
