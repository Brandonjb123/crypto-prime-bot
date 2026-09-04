"""Regression tests untuk validitas metodologi historical simulation."""

from datetime import UTC, datetime
from uuid import uuid4

from src.core.models.position import Position
from src.core.types.enums import PositionCloseReason, PositionStatus, Side
from src.simulation.historical_simulation import HistoricalSimulationRunner


def _make_position(side, entry, sl, tp1, tp2, size=1.0, status=PositionStatus.OPEN):
    return Position(
        position_id=uuid4(),
        execution_id=uuid4(),
        order_id=uuid4(),
        symbol="BTC/USDT",
        side=side,
        status=status,
        entry_price=entry,
        stop_loss=sl,
        take_profit=tp2,
        tp1_price=tp1,
        tp2_price=tp2,
        position_size=size,
        opened_at=datetime.now(UTC),
        closed_at=None,
        close_reason=PositionCloseReason.NONE,
        last_price=None,
        last_updated=None,
    )


class TestSimulationMethodology:
    def _make_runner(self):
        # Buat runner dengan engine dummy; hanya menguji _check_touch
        return HistoricalSimulationRunner(
            indicator_engine=None,
            analysis_engine=None,
            decision_engine=None,
            validation_engine=None,
            risk_engine=None,
            signal_engine=None,
        )

    def test_long_same_candle_sl_priority(self):
        runner = self._make_runner()
        pos = _make_position(Side.LONG, entry=100, sl=95, tp1=110, tp2=120)
        action, fraction, exit_price = runner._check_touch(pos, high_price=130, low_price=94)
        assert action == "SL"
        assert fraction == 1.0
        assert exit_price == 95

    def test_long_tp1_trigger(self):
        runner = self._make_runner()
        pos = _make_position(Side.LONG, entry=100, sl=95, tp1=110, tp2=120)
        action, fraction, exit_price = runner._check_touch(pos, high_price=115, low_price=100)
        assert action == "TP1"
        assert fraction == 0.5
        assert exit_price == 110

    def test_long_tp2_trigger(self):
        runner = self._make_runner()
        pos = _make_position(Side.LONG, entry=100, sl=95, tp1=110, tp2=120)
        action, fraction, exit_price = runner._check_touch(pos, high_price=125, low_price=100)
        assert action == "TP2"
        assert fraction == 1.0
        assert exit_price == 120

    def test_short_same_candle_sl_priority(self):
        runner = self._make_runner()
        pos = _make_position(Side.SHORT, entry=100, sl=105, tp1=90, tp2=80)
        action, fraction, exit_price = runner._check_touch(pos, high_price=106, low_price=79)
        assert action == "SL"
        assert fraction == 1.0
        assert exit_price == 105

    def test_short_tp1_trigger(self):
        runner = self._make_runner()
        pos = _make_position(Side.SHORT, entry=100, sl=105, tp1=90, tp2=80)
        action, fraction, exit_price = runner._check_touch(pos, high_price=100, low_price=85)
        assert action == "TP1"
        assert fraction == 0.5
        assert exit_price == 90

    def test_hold_when_no_touch(self):
        runner = self._make_runner()
        pos = _make_position(Side.LONG, entry=100, sl=95, tp1=110, tp2=120)
        action, fraction, exit_price = runner._check_touch(pos, high_price=105, low_price=96)
        assert action == "HOLD"
        assert fraction == 0.0
        assert exit_price == 0.0