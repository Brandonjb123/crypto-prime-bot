"""Volume Engine — klasifikasi volume spike."""

from datetime import UTC, datetime

from src.core.models.market_intelligence import VolumeAnalysis
from src.core.models.normalized_asset import NormalizedAsset
from src.core.types.enums import VolumeSignal


class VolumeEngine:
    """Analisis volume spike dari NormalizedAsset."""

    SPIKE_THRESHOLD = 2.0  # >= 2.0 → SPIKE
    NORMAL_THRESHOLD = 1.0  # 1.0 - 2.0 → NORMAL, < 1.0 → WEAK

    def analyze(self, asset: NormalizedAsset) -> VolumeAnalysis:
        """Klasifikasi volume spike ratio."""
        ratio = asset.volume_spike_ratio

        if ratio >= self.SPIKE_THRESHOLD:
            state = VolumeSignal.SPIKE
        elif ratio >= self.NORMAL_THRESHOLD:
            state = VolumeSignal.NORMAL
        else:
            state = VolumeSignal.WEAK

        # Confidence: semakin tinggi spike, semakin yakin (capped at 1.0)
        confidence = min(ratio / 2.0, 1.0)

        return VolumeAnalysis(
            state=state,
            spike_ratio=ratio,
            confidence_score=confidence,
            timestamp=datetime.now(UTC),
        )
