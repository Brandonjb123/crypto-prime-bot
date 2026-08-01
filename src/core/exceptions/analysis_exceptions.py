class AnalysisError(Exception):
    """Base exception untuk semua analysis errors."""


class AnalysisFailedError(AnalysisError):
    """Analisis gagal total (LLM timeout, parsing error, dll)."""


class InconsistentDataError(AnalysisError):
    """Data dari berbagai source tidak konsisten."""


class UnsupportedPairError(AnalysisError):
    """Pair tidak didukung untuk analisis."""