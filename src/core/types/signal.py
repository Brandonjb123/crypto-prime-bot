from typing import Optional
from pydantic import BaseModel
from src.core.types.enums import Side, Verdict, ConfidenceLevel


class AnalysisResult(BaseModel):
    """Result dari satu modul analisis."""
    module: str
    score: float
    details: Optional[str] = None


class Signal(BaseModel):
    """Signal trading final setelah semua analisis."""
    pair: str
    side: Side
    verdict: Verdict
    entry_price: Optional[float] = None
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    analysis_results: list[AnalysisResult] = []
    summary: Optional[str] = None
    risk_notes: Optional[str] = None