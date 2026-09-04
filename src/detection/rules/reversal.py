"""Reversal Rule — CHoCH + sentiment shift."""

from src.core.models.snapshot import AnalysisSnapshot
from src.core.types.enums import MarketStructure, SentimentLevel, TrendDirection, VolumeSignal
from src.detection.rules.base_rule import BaseRule, RuleResult


class ReversalRule(BaseRule):
    """Rule: Reversal (CHoCH + sentiment shift + volume)."""

    @property
    def name(self) -> str:
        return "reversal"

    def evaluate(self, snapshot: AnalysisSnapshot) -> RuleResult:
        reasons: list[str] = []
        passed = True

        # 1. Structure harus CHOCH
        if snapshot.structure.structure != MarketStructure.CHOCH:
            return RuleResult(
                passed=False,
                reasons=[f"Structure {snapshot.structure.structure.value} — bukan CHOCH"],
            )

        reasons.append("CHoCH terdeteksi — potensi reversal")

        # 2. Tentukan arah berdasarkan CHOCH + trend
        if snapshot.trend == TrendDirection.BULLISH:
            direction = "LONG"
            reasons.append("Trend BULLISH — reversal ke atas")
        elif snapshot.trend == TrendDirection.BEARISH:
            direction = "SHORT"
            reasons.append("Trend BEARISH — reversal ke bawah")
        else:
            return RuleResult(passed=False, reasons=["Trend SIDEWAYS — reversal tidak jelas"])

        # 3. Sentiment harus berlawanan dengan trend sebelumnya (konfirmasi reversal)
        if snapshot.trend == TrendDirection.BULLISH:
            if snapshot.sentiment.overall not in (SentimentLevel.GREED, SentimentLevel.NEUTRAL):
                reasons.append(
                    f"Sentiment {snapshot.sentiment.overall.value} — tidak mendukung reversal bullish"
                )
                passed = False
            else:
                reasons.append("Sentiment mendukung reversal bullish")
        else:
            if snapshot.sentiment.overall not in (SentimentLevel.FEAR, SentimentLevel.NEUTRAL):
                reasons.append(
                    f"Sentiment {snapshot.sentiment.overall.value} — tidak mendukung reversal bearish"
                )
                passed = False
            else:
                reasons.append("Sentiment mendukung reversal bearish")

        # 4. Volume NORMAL atau SPIKE
        if snapshot.volume.state == VolumeSignal.WEAK:
            reasons.append("Volume WEAK — reversal butuh konfirmasi volume")
            passed = False
        else:
            reasons.append(f"Volume {snapshot.volume.state.value} — cukup untuk reversal")

        # 5. Confidence >= 0.70 (threshold lebih tinggi)
        if snapshot.confidence.score < 0.70:
            reasons.append(f"Confidence score {snapshot.confidence.score:.2f} < 0.70")
            passed = False
        else:
            reasons.append(
                f"Confidence score {snapshot.confidence.score:.2f} — memadai untuk reversal"
            )

        return RuleResult(
            passed=passed,
            direction=direction if passed else None,
            reasons=reasons,
        )
