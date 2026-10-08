"""ActionabilityEvaluator — read-only transient evaluation of ACTIVE lifecycles.

Evaluasi expiry (persisted transition ACTIVE → EXPIRED/TIME) dan range state
(transient, tidak dipersist). Terpisah dari PriceRefreshService.
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID

from loguru import logger

from src.core.models.signal_lifecycle import SignalLifecycle
from src.core.types.enums import SignalLifecycleExpireReason
from src.storage.repositories.signal_lifecycle_repository import (
    SignalLifecycleRepository,
)


class RangeState(StrEnum):
    IN_RANGE = "IN_RANGE"
    OUT_OF_RANGE = "OUT_OF_RANGE"
    UNKNOWN = "UNKNOWN"
    EXPIRED = "EXPIRED"


@dataclass(frozen=True)
class LifecycleEvaluation:
    """Transient evaluation result. Tidak dipersist."""

    signal_id: UUID
    symbol: str
    range_state: RangeState
    current_price: float | None


class ActionabilityEvaluator:
    """Evaluator lifecycle ACTIVE: expiry + transient range state."""

    def __init__(
        self,
        repository: SignalLifecycleRepository,
        price_provider,
    ) -> None:
        self.repository = repository
        self.price_provider = price_provider

    def evaluate_once(self) -> list[LifecycleEvaluation]:
        """Evaluate semua ACTIVE lifecycle. Idempotent.

        Return list hasil transient. Expiry takes precedence over range.
        """
        now = datetime.now(UTC)
        active_lifecycles = self.repository.get_all_active()
        results: list[LifecycleEvaluation] = []

        for lifecycle in active_lifecycles:
            results.append(self._evaluate_single(lifecycle, now))

        return results

    def _evaluate_single(
        self, lifecycle: SignalLifecycle, now: datetime
    ) -> LifecycleEvaluation:
        # Expiry takes precedence — skip range evaluation entirely
        if now >= lifecycle.expires_at:
            try:
                self.repository.mark_expired(
                    lifecycle.signal_id, SignalLifecycleExpireReason.TIME
                )
                logger.info(
                    f"[actionability] lifecycle expired (TIME): {lifecycle.signal_id}"
                )
            except Exception as e:
                logger.error(
                    f"[actionability] mark_expired failed for "
                    f"{lifecycle.signal_id}: {e}"
                )
            return LifecycleEvaluation(
                signal_id=lifecycle.signal_id,
                symbol=lifecycle.symbol,
                range_state=RangeState.EXPIRED,
                current_price=None,
            )

        # Range evaluation (transient)
        current_price = self.price_provider.get_price(lifecycle.symbol)
        if current_price is None:
            return LifecycleEvaluation(
                signal_id=lifecycle.signal_id,
                symbol=lifecycle.symbol,
                range_state=RangeState.UNKNOWN,
                current_price=None,
            )

        if lifecycle.zone_low <= current_price <= lifecycle.zone_high:
            state = RangeState.IN_RANGE
        else:
            state = RangeState.OUT_OF_RANGE

        return LifecycleEvaluation(
            signal_id=lifecycle.signal_id,
            symbol=lifecycle.symbol,
            range_state=state,
            current_price=current_price,
        )