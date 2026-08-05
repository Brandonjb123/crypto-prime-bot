"""Setup Detection Engine — orchestrator dengan rule registry."""

from datetime import UTC, datetime

from src.core.models.setup import SetupResult
from src.core.models.snapshot import AnalysisSnapshot
from src.core.types.enums import Side
from src.detection.rules.base_rule import BaseRule
from src.detection.rules.breakout import BreakoutRule
from src.detection.rules.reversal import ReversalRule
from src.detection.rules.trend_following import TrendFollowingRule


class SetupDetector:
    """Deteksi trade setup dari AnalysisSnapshot menggunakan rule registry."""

    # Prioritas: Reversal > Breakout > TrendFollowing
    PRIORITY_ORDER = ["reversal", "breakout", "trend_following"]

    def __init__(self) -> None:
        self.registry: list[BaseRule] = [
            TrendFollowingRule(),
            BreakoutRule(),
            ReversalRule(),
        ]

    def detect(self, snapshot: AnalysisSnapshot) -> SetupResult:
        """Evaluasi semua rules, pilih setup terbaik."""
        triggered: list[BaseRule] = []
        failed_rules: list[str] = []
        all_reasons: list[str] = []

        for rule in self.registry:
            result = rule.evaluate(snapshot)
            if result.passed:
                triggered.append(rule)
                all_reasons.extend(result.reasons)
            else:
                failed_rules.append(rule.name)

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

        # Konversi direction string ke Side enum
        direction = Side.LONG if best_result.direction == "LONG" else Side.SHORT

        return SetupResult(
            direction=direction,
            setup_type=best_rule.name,
            triggered_rules=[r.name for r in triggered],
            failed_rules=failed_rules,
            confidence_score=snapshot.confidence.score,
            confidence_level=snapshot.confidence.level,
            blocked_reasons=snapshot.confidence.blocked_reasons,
            is_valid_setup=not snapshot.confidence.blocked_reasons,
            reasoning=all_reasons,
            timestamp=datetime.now(UTC),
        )

    def _select_best(self, triggered: list[BaseRule]) -> BaseRule:
        """Pilih rule terbaik berdasarkan prioritas."""
        for priority in self.PRIORITY_ORDER:
            for rule in triggered:
                if rule.name == priority:
                    return rule
        return triggered[0]