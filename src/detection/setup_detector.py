"""Setup Detection Engine — orchestrator dengan rule registry."""

from datetime import UTC, datetime

from config.constants import RULE_PRIORITY_ORDER
from src.core.models.setup import SetupResult
from src.core.models.snapshot import AnalysisSnapshot
from src.core.types.enums import RuleType, SetupType, Side
from src.detection.rules.base_rule import BaseRule
from src.detection.rules.breakout import BreakoutRule
from src.detection.rules.reversal import ReversalRule
from src.detection.rules.trend_following import TrendFollowingRule

# Mapping str → enum
RULE_TYPE_MAP: dict[str, RuleType] = {
    "trend_following": RuleType.TREND_FOLLOWING,
    "breakout": RuleType.BREAKOUT,
    "reversal": RuleType.REVERSAL,
}

SETUP_TYPE_MAP: dict[str, SetupType] = {
    "trend_following": SetupType.TREND_FOLLOWING,
    "breakout": SetupType.BREAKOUT,
    "reversal": SetupType.REVERSAL,
}


class SetupDetector:
    """Deteksi trade setup dari AnalysisSnapshot menggunakan rule registry."""

    def __init__(self) -> None:
        self.registry: list[BaseRule] = [
            TrendFollowingRule(),
            BreakoutRule(),
            ReversalRule(),
        ]

    def detect(self, snapshot: AnalysisSnapshot) -> SetupResult:
        """Evaluasi semua rules, pilih setup terbaik."""
        triggered: list[BaseRule] = []
        failed_rules: list[RuleType] = []
        all_reasons: list[str] = []

        for rule in self.registry:
            result = rule.evaluate(snapshot)
            if result.passed:
                triggered.append(rule)
                all_reasons.extend(result.reasons)
            else:
                failed_rules.append(RULE_TYPE_MAP.get(rule.name, RuleType.TREND_FOLLOWING))

        # ── Tidak ada rule yang lolos ──
        if not triggered:
            return SetupResult(
                direction=None,
                setup_type=None,
                triggered_rules=[],
                failed_rules=failed_rules,
                confidence_score=snapshot.confidence.score,
                confidence_level=snapshot.confidence.level,
                blocked_reasons=snapshot.confidence.blocked_reasons,
                is_valid_setup=False,
                reasoning=["Tidak ada rule yang lolos"],
                timestamp=datetime.now(UTC),
            )

        # ── Pilih rule terbaik ──
        best_rule = self._select_best(triggered)
        best_result = best_rule.evaluate(snapshot)

        direction = Side.LONG if best_result.direction == "LONG" else Side.SHORT

        # is_valid_setup: hanya dari detection, bukan execution permission
        is_valid = direction is not None

        return SetupResult(
            direction=direction,
            setup_type=SETUP_TYPE_MAP.get(best_rule.name),
            triggered_rules=[RULE_TYPE_MAP[r.name] for r in triggered],
            failed_rules=failed_rules,
            confidence_score=snapshot.confidence.score,
            confidence_level=snapshot.confidence.level,
            blocked_reasons=snapshot.confidence.blocked_reasons,
            is_valid_setup=is_valid,
            reasoning=all_reasons,
            timestamp=datetime.now(UTC),
        )

    def _select_best(self, triggered: list[BaseRule]) -> BaseRule:
        """Pilih rule terbaik berdasarkan prioritas dari config."""
        for priority in RULE_PRIORITY_ORDER:
            for rule in triggered:
                if rule.name == priority:
                    return rule
        return triggered[0]
