"""Risk Gate — pre-execution safety checks."""


class RiskGate:
    def check(self, signal, portfolio=None, daily_stats=None) -> bool:
        """Phase 1: selalu allow. Akan diimplementasikan di Phase 2."""
        return True