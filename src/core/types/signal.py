from pydantic import BaseModel

from src.core.types.enums import ConfidenceLevel, Side, Verdict


class AnalysisResult(BaseModel):
    """Result dari satu modul analisis."""

    module: str
    score: float
    details: str | None = None


class Signal(BaseModel):
    """Signal trading final setelah semua analisis."""

    pair: str
    side: Side
    verdict: Verdict
    entry_price: float | None = None
    target_price: float | None = None
    stop_loss: float | None = None
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    analysis_results: list[AnalysisResult] = []
    summary: str | None = None
    risk_notes: str | None = None
