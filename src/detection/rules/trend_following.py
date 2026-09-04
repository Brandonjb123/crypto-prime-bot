"""Trend Following Rule — EMA aligned + BOS + Volume."""

from src.core.models.snapshot import AnalysisSnapshot
from src.core.types.enums import MarketStructure, TrendDirection, VolumeSignal
from src.detection.rules.base_rule import BaseRule, RuleResult


class TrendFollowingRule(BaseRule):
    """Rule: Trend Following (EMA + BOS + Volume)."""

    @property
    def name(self) -> str:
        return "trend_following"

    def evaluate(self, snapshot: AnalysisSnapshot) -> RuleResult:
        reasons: list[str] = []
        passed = True

        # 1. Trend bukan SIDEWAYS
        if snapshot.trend == TrendDirection.SIDEWAYS:
            return RuleResult(passed=False, reasons=["Trend SIDEWAYS — tidak ada arah jelas"])

        # 2. Structure BOS aligned dengan trend
        if snapshot.trend == TrendDirection.BULLISH:
            if snapshot.structure.structure != MarketStructure.BOS_BULLISH:
                reasons.append("Structure tidak BOS_BULLISH")
                passed = False
            else:
                reasons.append("Trend BULLISH + BOS_BULLISH aligned")
                direction = "LONG"
        else:  # BEARISH
            if snapshot.structure.structure != MarketStructure.BOS_BEARISH:
                reasons.append("Structure tidak BOS_BEARISH")
                passed = False
            else:
                reasons.append("Trend BEARISH + BOS_BEARISH aligned")
                direction = "SHORT"

        # 3. Volume bukan WEAK
        if snapshot.volume.state == VolumeSignal.WEAK:
            reasons.append("Volume WEAK")
            passed = False
        else:
            reasons.append(f"Volume {snapshot.volume.state.value} — cukup")

        # 4. Confidence score >= 0.60
        if snapshot.confidence.score < 0.60:
            reasons.append(f"Confidence score {snapshot.confidence.score:.2f} < 0.60")
            passed = False
        else:
            reasons.append(f"Confidence score {snapshot.confidence.score:.2f} — memadai")

        # 5. Blocked reasons kosong
        if snapshot.confidence.blocked_reasons:
            reasons.append("Ada blocked reasons dari Confidence Engine")
            passed = False

        return RuleResult(
            passed=passed,
            direction=direction if passed else None,
            reasons=reasons,
        )
