"""Unit tests untuk lifecycle label di /lastsignal dan /signals (H3.2)."""

from datetime import UTC, datetime
from uuid import uuid4

from src.telegram.command_handler import last_signal_handler, signals_handler


class _Sig:
    def __init__(self, symbol="BTC"):
        self.signal_id = uuid4()
        self.symbol = symbol
        self.side = "BUY"
        self.status = "ACTIVE"
        self.entry_price = 100.0
        self.stop_loss = 95.0
        self.take_profit = 110.0
        self.confidence = 80
        self.risk_level = "MEDIUM"
        self.position_size = 1.0
        self.reasoning = []
        self.created_at = datetime.now(UTC)


class _Repo:
    def __init__(self, signals=None, lifecycle_map=None, raises=False):
        self._signals = signals or []
        self._lifecycle = lifecycle_map or {}
        self._raises = raises

    def history(self, **kwargs):
        return list(self._signals)

    def latest_by_symbol(self, symbol):
        for s in self._signals:
            if s.symbol == symbol:
                return s
        return None

    def get_lifecycle_states(self, ids):
        if self._raises:
            raise RuntimeError("db down")
        return {sid: self._lifecycle[sid] for sid in ids if sid in self._lifecycle}


def _ctx(repo):
    return {"signal_repository": repo}


class TestLastSignalHandler:
    def test_expired_renders_stale(self):
        s = _Sig()
        repo = _Repo([s], lifecycle_map={s.signal_id: "EXPIRED"})
        resp = last_signal_handler(None, _ctx(repo))
        assert "STALE" in resp.text

    def test_active_renders_normal(self):
        s = _Sig()
        repo = _Repo([s], lifecycle_map={s.signal_id: "ACTIVE"})
        resp = last_signal_handler(None, _ctx(repo))
        assert "STALE" not in resp.text
        assert "LEGACY" not in resp.text

    def test_legacy_renders_legacy(self):
        s = _Sig()
        repo = _Repo([s], lifecycle_map={})
        resp = last_signal_handler(None, _ctx(repo))
        assert "LEGACY" in resp.text

    def test_query_failure_renders_unknown(self):
        s = _Sig()
        repo = _Repo([s], raises=True)
        resp = last_signal_handler(None, _ctx(repo))
        assert "unavailable" in resp.text

    def test_no_repo(self):
        resp = last_signal_handler(None, {})
        assert "Belum ada sinyal aktif" in resp.text or "Belum ada sinyal" in resp.text


class TestSignalsHandler:
    def test_mixed_states(self):
        a, b, c = _Sig("BTC"), _Sig("ETH"), _Sig("SOL")
        # a = ACTIVE (row ada, status ACTIVE)
        # b = EXPIRED (row ada, status EXPIRED)
        # c = LEGACY (tidak ada row — jadi tidak muncul di lifecycle_map)
        repo = _Repo(
            [a, b, c],
            lifecycle_map={
                a.signal_id: "ACTIVE",
                b.signal_id: "EXPIRED",
            },
        )
        resp = signals_handler(None, _ctx(repo))
        assert "STALE" in resp.text
        assert "LEGACY" in resp.text

    def test_query_failure_renders_unknown(self):
        a = _Sig("BTC")
        repo = _Repo([a], raises=True)
        resp = signals_handler(None, _ctx(repo))
        assert "unavailable" in resp.text