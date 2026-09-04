"""Breakout Rule — BOS + Volume spike + price position."""

from src.core.models.snapshot import AnalysisSnapshot
from src.core.types.enums import MarketStructure, VolumeSignal
from src.detection.rules.base_rule import BaseRule, RuleResult


class BreakoutRule(BaseRule):
    """Rule: Breakout (BOS + Volume SPIKE + favorable price position)."""

    @property
    def name(self) -> str:
        return "breakout"

    def evaluate(self, snapshot: AnalysisSnapshot) -> RuleResult:
        reasons: list[str] = []
        passed = True

        # 1. Structure harus BOS (bullish atau bearish)
        if snapshot.structure.structure == MarketStructure.BOS_BULLISH:
            reasons.append("BOS_BULLISH terdeteksi")
            direction = "LONG"
        elif snapshot.structure.structure == MarketStructure.BOS_BEARISH:
            reasons.append("BOS_BEARISH terdeteksi")
            direction = "SHORT"
        else:
            return RuleResult(
                passed=False,
                reasons=[f"Structure {snapshot.structure.structure.value} — bukan BOS"],
            )

        # 2. Volume harus SPIKE
        if snapshot.volume.state != VolumeSignal.SPIKE:
            reasons.append(f"Volume {snapshot.volume.state.value} — bukan SPIKE")
            passed = False
        else:
            reasons.append("Volume SPIKE — momentum kuat")

        # 3. Price position favorable
        pos = snapshot.support_resistance.price_position
        if direction == "LONG" and pos is not None and pos > 0.7:
            reasons.append(f"Price position {pos:.2f} > 0.7 — dekat resistance untuk LONG")
            passed = False
        elif direction == "SHORT" and pos is not None and pos < 0.3:
            reasons.append(f"Price position {pos:.2f} < 0.3 — dekat support untuk SHORT")
            passed = False
        elif pos is not None:
            reasons.append(f"Price position {pos:.2f} — favorable")

        # 4. Confidence >= 0.65
        if snapshot.confidence.score < 0.65:
            reasons.append(f"Confidence score {snapshot.confidence.score:.2f} < 0.65")
            passed = False
        else:
            reasons.append(f"Confidence score {snapshot.confidence.score:.2f} — memadai")

        return RuleResult(
            passed=passed,
            direction=direction if passed else None,
            reasons=reasons,
        )
