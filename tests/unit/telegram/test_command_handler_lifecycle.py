"""Unit tests untuk lifecycle label di /lastsignal dan /signals (H3.2 R2)."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from src.core.models.lifecycle_lookup import (
    LifecycleLookupResult,
    LifecycleRecord,
)
from src.telegram.command_handler import last_signal_handler, signals_handler
from src.telegram.lifecycle_display import LIFECYCLE_EPOCH_UTC

FUTURE = datetime.now(UTC) + timedelta(hours=1)
PAST = datetime.now(UTC) - timedelta(hours=1)
PRE_EPOCH = LIFECYCLE_EPOCH_UTC - timedelta(days=1)
POST_EPOCH = LIFECYCLE_EPOCH_UTC + timedelta(hours=1)


class _Sig:
    def __init__(self, symbol="BTC", status="ACTIVE", created_at=None):
        self.signal_id = uuid4()
        self.symbol = symbol
        self.side = "BUY"
        self.status = status
        self.entry_price = 100.0
        self.stop_loss = 95.0
        self.take_profit = 110.0
        self.confidence = 80
        self.risk_level = "MEDIUM"
        self.position_size = 1.0
        self.reasoning = []
        self.created_at = created_at or POST_EPOCH


class _SignalRepo:
    def __init__(self, signals=None):
        self._signals = signals or []

    def history(self, **kwargs):
        return list(self._signals)

    def latest_by_symbol(self, symbol):
        for s in self._signals:
            if s.symbol == symbol:
                return s
        return None


class _LifecycleRepo:
    def __init__(self, records=None, failed=None, raises=False):
        self._records = records or {}
        self._failed = failed or set()
        self._raises = raises

    def get_lifecycle_lookup(self, signal_ids):
        if self._raises:
            raise RuntimeError("db down")
        found = {sid: self._records[sid] for sid in signal_ids if sid in self._records}
        failed = {sid for sid in signal_ids if sid in self._failed}
        absent = {sid for sid in signal_ids if sid not in found and sid not in failed}
        return LifecycleLookupResult(found=found, absent=absent, failed=failed)


def _ctx(signal_repo, lifecycle_repo):
    return {
        "signal_repository": signal_repo,
        "signal_lifecycle_repository": lifecycle_repo,
    }


class TestLastSignalHandler:
    def test_expired_renders_stale(self):
        s = _Sig()
        sig_repo = _SignalRepo([s])
        lc_repo = _LifecycleRepo(records={s.signal_id: LifecycleRecord(s.signal_id, "EXPIRED", None)})
        resp = last_signal_handler(None, _ctx(sig_repo, lc_repo))
        assert "STALE" in resp.text

    def test_active_renders_normal(self):
        s = _Sig()
        sig_repo = _SignalRepo([s])
        lc_repo = _LifecycleRepo(records={s.signal_id: LifecycleRecord(s.signal_id, "ACTIVE", FUTURE)})
        resp = last_signal_handler(None, _ctx(sig_repo, lc_repo))
        assert "STALE" not in resp.text
        assert "LEGACY" not in resp.text

    def test_legacy_renders_legacy(self):
        s = _Sig(created_at=PRE_EPOCH)
        sig_repo = _SignalRepo([s])
        lc_repo = _LifecycleRepo()
        resp = last_signal_handler(None, _ctx(sig_repo, lc_repo))
        assert "LEGACY" in resp.text

    def test_recent_renders_conservatively(self):
        """B1: RECENT must render like UNKNOWN — never as actionable ACTIVE."""
        s = _Sig(created_at=POST_EPOCH)
        sig_repo = _SignalRepo([s])
        lc_repo = _LifecycleRepo()
        resp = last_signal_handler(None, _ctx(sig_repo, lc_repo))
        assert "LEGACY" not in resp.text
        assert "STALE" not in resp.text
        # B1: must show conservative "unavailable" wording
        assert "unavailable" in resp.text

    def test_query_failure_renders_unknown(self):
        s = _Sig()
        sig_repo = _SignalRepo([s])
        lc_repo = _LifecycleRepo(raises=True)
        resp = last_signal_handler(None, _ctx(sig_repo, lc_repo))
        assert "unavailable" in resp.text

    def test_no_repo(self):
        resp = last_signal_handler(None, {})
        assert "Belum ada sinyal" in resp.text

    def test_no_lifecycle_repo_renders_unknown(self):
        s = _Sig()
        sig_repo = _SignalRepo([s])
        resp = last_signal_handler(None, {"signal_repository": sig_repo})
        assert "unavailable" in resp.text


class TestSignalsHandler:
    def test_mixed_states(self):
        a = _Sig("BTC")
        b = _Sig("ETH")
        c = _Sig("SOL", created_at=PRE_EPOCH)
        sig_repo = _SignalRepo([a, b, c])
        lc_repo = _LifecycleRepo(
            records={
                a.signal_id: LifecycleRecord(a.signal_id, "ACTIVE", FUTURE),
                b.signal_id: LifecycleRecord(b.signal_id, "EXPIRED", None),
            }
        )
        resp = signals_handler(None, _ctx(sig_repo, lc_repo))
        assert "STALE" in resp.text
        assert "LEGACY" in resp.text

    def test_query_failure_renders_unknown(self):
        a = _Sig("BTC")
        sig_repo = _SignalRepo([a])
        lc_repo = _LifecycleRepo(raises=True)
        resp = signals_handler(None, _ctx(sig_repo, lc_repo))
        assert "unavailable" in resp.text

class TestSkippedInvalidBypassLifecycle:
    """R9: SKIPPED/INVALID must not trigger lifecycle lookup or warning."""

    def test_lastsignal_skipped_skips_lookup(self):
        s = _Sig(status="SKIPPED")

        class _ProbeLifecycle:
            def __init__(self):
                self.called = False

            def get_lifecycle_lookup(self, signal_ids):
                self.called = True
                raise AssertionError("lifecycle lookup must not be called")

        probe = _ProbeLifecycle()
        sig_repo = _SignalRepo([s])
        resp = last_signal_handler(
            None,
            {
                "signal_repository": sig_repo,
                "signal_lifecycle_repository": probe,
            },
        )
        assert probe.called is False
        assert "WAIT" in resp.text or "SKIPPED" in resp.text
        assert "lifecycle state unavailable" not in resp.text
        assert "STALE" not in resp.text
        assert "LEGACY" not in resp.text

    def test_lastsignal_invalid_skips_lookup(self):
        s = _Sig(status="INVALID")

        class _ProbeLifecycle:
            def __init__(self):
                self.called = False

            def get_lifecycle_lookup(self, signal_ids):
                self.called = True
                raise AssertionError("lifecycle lookup must not be called")

        probe = _ProbeLifecycle()
        sig_repo = _SignalRepo([s])
        resp = last_signal_handler(
            None,
            {
                "signal_repository": sig_repo,
                "signal_lifecycle_repository": probe,
            },
        )
        assert probe.called is False
        assert "INVALID" in resp.text
        assert "lifecycle state unavailable" not in resp.text
        assert "STALE" not in resp.text
        assert "LEGACY" not in resp.text        