"""AnalysisSnapshot — kontrak antar layer."""

from datetime import datetime

from pydantic import BaseModel

from src.core.models.analysis import TechnicalAnalysis
from src.core.models.confidence import ConfidenceResult
from src.core.models.market_intelligence import (
    FuturesAnalysis,
    SentimentAnalysis,
    SupportResistanceResult,
    VolatilityAnalysis,
    VolumeAnalysis,
)
from src.core.models.structure import MarketStructureResult
from src.core.types.enums import TrendDirection


class AnalysisSnapshot(BaseModel):
    """Snapshot lengkap semua hasil analisis untuk satu symbol."""

    symbol: str
    price: float
    technical: TechnicalAnalysis
    trend: TrendDirection
    structure: MarketStructureResult
    volume: VolumeAnalysis
    futures: FuturesAnalysis
    volatility: VolatilityAnalysis
    support_resistance: SupportResistanceResult
    sentiment: SentimentAnalysis
    confidence: ConfidenceResult
    timestamp: datetime