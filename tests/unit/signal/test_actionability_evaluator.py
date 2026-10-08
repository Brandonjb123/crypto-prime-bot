"""Tests untuk ActionabilityEvaluator — expiry + transient range evaluation."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from src.core.models.signal_lifecycle import SignalLifecycle
from src.core.types.enums import (
    SignalLifecycleExpireReason,
    SignalLifecycleStatus,
)
from src.signal.actionability_evaluator import (
    ActionabilityEvaluator,
    RangeState,
)


class _FakeRepo:
    """In-memory repo yang mimic signal_lifecycle_repository semantics."""

    def __init__(self) -> None:
        self._lifecycles: dict = {}
        self.mark_expired_calls: list = []

    def add(self, lifecycle: SignalLifecycle) -> None:
        self._lifecycles[lifecycle.signal_id] = lifecycle

    def get_all_active(self) -> list[SignalLifecycle]:
        return [
            lc
            for lc in self._lifecycles.values()
            if lc.status == SignalLifecycleStatus.ACTIVE
        ]

    def mark_expired(self, signal_id, reason) -> None:
        self.mark_expired_calls.append((signal_id, reason))
        lc = self._lifecycles.get(signal_id)
        if lc is None or lc.status != SignalLifecycleStatus.ACTIVE:
            return
        self._lifecycles[signal_id] = lc.model_copy(
            update={
                "status": SignalLifecycleStatus.EXPIRED,
                "expire_reason": reason,
                "terminal_at": datetime.now(UTC),
            }
        )


class _FakeProvider:
    def __init__(self, prices: dict | None = None) -> None:
        self._prices = prices or {}

    def get_price(self, symbol: str):
        return self._prices.get(symbol)


def _make_lifecycle(
    symbol: str = "BTC",
    zone_low: float = 100.0,
    zone_high: float = 110.0,
    expires_offset_seconds: int = 3600,
    status: SignalLifecycleStatus = SignalLifecycleStatus.ACTIVE,
):
    now = datetime.now(UTC)
    return SignalLifecycle(
        signal_id=uuid4(),
        symbol=symbol,
        status=status,
        expire_reason=(
            None
            if status == SignalLifecycleStatus.ACTIVE
            else SignalLifecycleExpireReason.TIME
        ),
        created_at=now,
        expires_at=now + timedelta(seconds=expires_offset_seconds),
        zone_low=zone_low,
        zone_high=zone_high,
        terminal_at=None if status == SignalLifecycleStatus.ACTIVE else now,
    )


# ---------- Expiry ----------


class TestExpiry:
    def test_before_deadline_remains_active(self):
        repo = _FakeRepo()
        lc = _make_lifecycle(expires_offset_seconds=3600)
        repo.add(lc)
        evaluator = ActionabilityEvaluator(repo, _FakeProvider({"BTC": 105.0}))

        evaluator.evaluate_once()

        assert repo.mark_expired_calls == []
        assert repo.get_all_active()[0].signal_id == lc.signal_id

    def test_exactly_deadline_marks_expired(self):
        repo = _FakeRepo()
        # expires_at = now (offset 0) → now >= expires_at true
        lc = _make_lifecycle(expires_offset_seconds=0)
        repo.add(lc)
        evaluator = ActionabilityEvaluator(repo, _FakeProvider({"BTC": 105.0}))

        results = evaluator.evaluate_once()

        assert len(repo.mark_expired_calls) == 1
        assert repo.mark_expired_calls[0][0] == lc.signal_id
        assert repo.mark_expired_calls[0][1] == SignalLifecycleExpireReason.TIME
        assert results[0].range_state == RangeState.EXPIRED

    def test_after_deadline_marks_expired(self):
        repo = _FakeRepo()
        lc = _make_lifecycle(expires_offset_seconds=-3600)
        repo.add(lc)
        evaluator = ActionabilityEvaluator(repo, _FakeProvider({"BTC": 105.0}))

        results = evaluator.evaluate_once()

        assert len(repo.mark_expired_calls) == 1
        assert results[0].range_state == RangeState.EXPIRED

    def test_already_non_active_ignored(self):
        repo = _FakeRepo()
        lc = _make_lifecycle(
            status=SignalLifecycleStatus.EXPIRED,
            expires_offset_seconds=-3600,
        )
        repo.add(lc)
        evaluator = ActionabilityEvaluator(repo, _FakeProvider({"BTC": 105.0}))

        results = evaluator.evaluate_once()

        assert repo.mark_expired_calls == []
        assert results == []

    def test_repeated_evaluation_idempotent(self):
        repo = _FakeRepo()
        lc = _make_lifecycle(expires_offset_seconds=-3600)
        repo.add(lc)
        evaluator = ActionabilityEvaluator(repo, _FakeProvider({"BTC": 105.0}))

        evaluator.evaluate_once()
        evaluator.evaluate_once()

        # Setelah iterasi pertama, lifecycle sudah EXPIRED.
        # Iterasi kedua tidak menemukan ACTIVE → tidak panggil mark_expired lagi.
        # Ini proof idempotency: repeated call aman, tidak dobel-mark.
        assert len(repo.mark_expired_calls) == 1
        assert repo.mark_expired_calls[0][1] == SignalLifecycleExpireReason.TIME
        assert repo.get_all_active() == []


# ---------- Range ----------


class TestRange:
    def test_price_at_zone_low_is_in_range(self):
        repo = _FakeRepo()
        repo.add(_make_lifecycle(zone_low=100.0, zone_high=110.0))
        evaluator = ActionabilityEvaluator(repo, _FakeProvider({"BTC": 100.0}))

        results = evaluator.evaluate_once()
        assert results[0].range_state == RangeState.IN_RANGE
        assert results[0].current_price == 100.0

    def test_price_at_zone_high_is_in_range(self):
        repo = _FakeRepo()
        repo.add(_make_lifecycle(zone_low=100.0, zone_high=110.0))
        evaluator = ActionabilityEvaluator(repo, _FakeProvider({"BTC": 110.0}))

        results = evaluator.evaluate_once()
        assert results[0].range_state == RangeState.IN_RANGE

    def test_price_inside_zone_is_in_range(self):
        repo = _FakeRepo()
        repo.add(_make_lifecycle(zone_low=100.0, zone_high=110.0))
        evaluator = ActionabilityEvaluator(repo, _FakeProvider({"BTC": 105.0}))

        results = evaluator.evaluate_once()
        assert results[0].range_state == RangeState.IN_RANGE

    def test_price_below_zone_is_out_of_range(self):
        repo = _FakeRepo()
        repo.add(_make_lifecycle(zone_low=100.0, zone_high=110.0))
        evaluator = ActionabilityEvaluator(repo, _FakeProvider({"BTC": 99.99}))

        results = evaluator.evaluate_once()
        assert results[0].range_state == RangeState.OUT_OF_RANGE

    def test_price_above_zone_is_out_of_range(self):
        repo = _FakeRepo()
        repo.add(_make_lifecycle(zone_low=100.0, zone_high=110.0))
        evaluator = ActionabilityEvaluator(repo, _FakeProvider({"BTC": 110.01}))

        results = evaluator.evaluate_once()
        assert results[0].range_state == RangeState.OUT_OF_RANGE

    def test_missing_price_yields_unknown(self):
        repo = _FakeRepo()
        repo.add(_make_lifecycle())
        evaluator = ActionabilityEvaluator(repo, _FakeProvider({}))

        results = evaluator.evaluate_once()
        assert results[0].range_state == RangeState.UNKNOWN
        assert results[0].current_price is None
        # Lifecycle tetap ACTIVE — tidak ada perubahan state
        assert len(repo.get_all_active()) == 1

    def test_expired_never_in_range(self):
        repo = _FakeRepo()
        # expires_at sudah lewat, price ada di dalam zone
        repo.add(_make_lifecycle(expires_offset_seconds=-10))
        evaluator = ActionabilityEvaluator(repo, _FakeProvider({"BTC": 105.0}))

        results = evaluator.evaluate_once()
        assert results[0].range_state == RangeState.EXPIRED

    def test_range_result_not_persisted(self):
        repo = _FakeRepo()
        lc = _make_lifecycle(zone_low=100.0, zone_high=110.0)
        repo.add(lc)
        evaluator = ActionabilityEvaluator(repo, _FakeProvider({"BTC": 105.0}))

        evaluator.evaluate_once()

        # Lifecycle di repo tidak berubah (status tetap ACTIVE, tidak ada field range)
        stored = repo.get_all_active()[0]
        assert stored.status == SignalLifecycleStatus.ACTIVE
        assert not hasattr(stored, "range_state")


# ---------- Multiple ----------


class TestMultipleLifecycles:
    def test_multiple_evaluated_in_one_cycle(self):
        repo = _FakeRepo()
        repo.add(_make_lifecycle(symbol="BTC", zone_low=100.0, zone_high=110.0))
        repo.add(_make_lifecycle(symbol="ETH", zone_low=200.0, zone_high=210.0))
        repo.add(_make_lifecycle(symbol="SOL", expires_offset_seconds=-10))
        evaluator = ActionabilityEvaluator(
            repo,
            _FakeProvider({"BTC": 105.0, "ETH": 250.0, "SOL": 100.0}),
        )

        results = evaluator.evaluate_once()
        assert len(results) == 3

        states = {r.symbol: r.range_state for r in results}
        assert states["BTC"] == RangeState.IN_RANGE
        assert states["ETH"] == RangeState.OUT_OF_RANGE
        assert states["SOL"] == RangeState.EXPIRED

    def test_evaluator_uses_get_all_active(self):
        repo = _FakeRepo()
        # 3 ACTIVE + 1 EXPIRED
        repo.add(_make_lifecycle(symbol="BTC"))
        repo.add(_make_lifecycle(symbol="ETH"))
        repo.add(_make_lifecycle(symbol="SOL"))
        repo.add(_make_lifecycle(
            symbol="XRP",
            status=SignalLifecycleStatus.EXPIRED,
        ))
        evaluator = ActionabilityEvaluator(
            repo, _FakeProvider({"BTC": 105.0, "ETH": 205.0, "SOL": 305.0})
        )

        results = evaluator.evaluate_once()
        assert len(results) == 3
        assert {r.symbol for r in results} == {"BTC", "ETH", "SOL"}