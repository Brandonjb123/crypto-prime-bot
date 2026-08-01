class SignalError(Exception):
    """Base exception untuk signal processing."""


class SignalValidationError(SignalError):
    """Signal gagal validasi."""


class InsufficientDataError(SignalError):
    """Data tidak cukup untuk generate signal."""


class SignalExpiredError(SignalError):
    """Signal sudah expired."""