"""Unit tests untuk lifecycle label di formatter (H3.2)."""

from datetime import UTC, datetime
from uuid import uuid4

from src.telegram.formatter import (
    format_signal,
    format_signal_card,
    format_signals_summary,
)


class _Sig:
    def __init__(self, **kwargs):
        self.signal_id = kwargs.get("signal_id", uuid4())
        self.symbol = kwargs.get("symbol", "BTC")
        self.side = kwargs.get("side", "BUY")
        self.status = kwargs.get("status", "ACTIVE")
        self.entry_price = kwargs.get("entry_price", 100.0)
        self.stop_loss = kwargs.get("stop_loss", 95.0)
        self.take_profit = kwargs.get("take_profit", 110.0)
        self.confidence = kwargs.get("confidence", 80)
        self.risk_level = kwargs.get("risk_level", "MEDIUM")
        self.position_size = kwargs.get("position_size", 1.0)
        self.reasoning = kwargs.get("reasoning", [])
        self.created_at = kwargs.get("created_at", datetime.now(UTC))


class TestFormatSignalLifecycle:
    def test_active_no_stale_label(self):
        out = format_signal(_Sig(), lifecycle_state="ACTIVE")
        assert "STALE" not in out
        assert "LEGACY" not in out

    def test_expired_has_stale_label(self):
        out = format_signal(_Sig(), lifecycle_state="EXPIRED")
        assert "STALE" in out

    def test_legacy_has_legacy_label(self):
        out = format_signal(_Sig(), lifecycle_state="LEGACY")
        assert "LEGACY" in out

    def test_unknown_has_unavailable_label(self):
        out = format_signal(_Sig(), lifecycle_state="UNKNOWN")
        assert "unavailable" in out

    def test_default_unknown_when_not_passed(self):
        out = format_signal(_Sig())
        assert "unavailable" in out

    def test_skipped_unaffected(self):
        out = format_signal(_Sig(status="SKIPPED"), lifecycle_state="EXPIRED")
        assert "SKIPPED" in out

    def test_invalid_unaffected(self):
        out = format_signal(_Sig(status="INVALID"), lifecycle_state="EXPIRED")
        assert "INVALID" in out


class TestFormatSignalCardLifecycle:
    def test_active_no_label(self):
        out = format_signal_card(_Sig(), lifecycle_state="ACTIVE")
        assert "STALE" not in out
        assert "LEGACY" not in out

    def test_expired_label(self):
        out = format_signal_card(_Sig(), lifecycle_state="EXPIRED")
        assert "STALE" in out

    def test_legacy_label(self):
        out = format_signal_card(_Sig(), lifecycle_state="LEGACY")
        assert "LEGACY" in out

    def test_default_unknown(self):
        out = format_signal_card(_Sig())
        assert "unavailable" in out


class TestFormatSignalsSummaryLifecycle:
    def test_active_state_renders_normal(self):
        s = _Sig()
        out = format_signals_summary([s], lifecycle_map={s.signal_id: "ACTIVE"})
        assert "STALE" not in out
        assert "LEGACY" not in out

    def test_expired_state_labeled(self):
        s = _Sig()
        out = format_signals_summary([s], lifecycle_map={s.signal_id: "EXPIRED"})
        assert "STALE" in out

    def test_legacy_state_labeled(self):
        s = _Sig()
        out = format_signals_summary([s], lifecycle_map={s.signal_id: "LEGACY"})
        assert "LEGACY" in out

    def test_no_map_defaults_unknown(self):
        s = _Sig()
        out = format_signals_summary([s])
        assert "unavailable" in out

    def test_mixed_summary(self):
        a, b, c = _Sig(), _Sig(), _Sig()
        out = format_signals_summary(
            [a, b, c],
            lifecycle_map={
                a.signal_id: "ACTIVE",
                b.signal_id: "EXPIRED",
                c.signal_id: "LEGACY",
            },
        )
        assert "STALE" in out
        assert "LEGACY" in out