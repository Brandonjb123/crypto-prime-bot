"""Unit tests untuk resolve_lifecycle_states (H3.2)."""

from uuid import uuid4

from src.telegram.lifecycle_display import (
    LIFECYCLE_ACTIVE,
    LIFECYCLE_EXPIRED,
    LIFECYCLE_LEGACY,
    LIFECYCLE_UNKNOWN,
    resolve_lifecycle_states,
)


class _StubRepo:
    def __init__(self, mapping=None, raises=None):
        self.mapping = mapping or {}
        self.raises = raises

    def get_lifecycle_states(self, signal_ids):
        if self.raises is not None:
            raise self.raises
        return {sid: self.mapping[sid] for sid in signal_ids if sid in self.mapping}


class TestResolveLifecycleStates:
    def test_empty_input(self):
        repo = _StubRepo()
        assert resolve_lifecycle_states(repo, []) == {}

    def test_active(self):
        sid = uuid4()
        repo = _StubRepo({sid: "ACTIVE"})
        assert resolve_lifecycle_states(repo, [sid]) == {sid: LIFECYCLE_ACTIVE}

    def test_expired(self):
        sid = uuid4()
        repo = _StubRepo({sid: "EXPIRED"})
        assert resolve_lifecycle_states(repo, [sid]) == {sid: LIFECYCLE_EXPIRED}

    def test_missing_key_becomes_legacy(self):
        sid = uuid4()
        repo = _StubRepo({})
        assert resolve_lifecycle_states(repo, [sid]) == {sid: LIFECYCLE_LEGACY}

    def test_query_failure_becomes_unknown(self):
        sid = uuid4()
        repo = _StubRepo(raises=RuntimeError("db down"))
        result = resolve_lifecycle_states(repo, [sid])
        assert result == {sid: LIFECYCLE_UNKNOWN}

    def test_unrecognized_state_becomes_unknown(self):
        sid = uuid4()
        repo = _StubRepo({sid: "WEIRD"})
        result = resolve_lifecycle_states(repo, [sid])
        assert result == {sid: LIFECYCLE_UNKNOWN}

    def test_dedup_input(self):
        sid = uuid4()
        repo = _StubRepo({sid: "ACTIVE"})
        result = resolve_lifecycle_states(repo, [sid, sid, sid])
        assert result == {sid: LIFECYCLE_ACTIVE}

    def test_mixed_states(self):
        a, b, c = uuid4(), uuid4(), uuid4()
        repo = _StubRepo({a: "ACTIVE", b: "EXPIRED"})
        result = resolve_lifecycle_states(repo, [a, b, c])
        assert result == {
            a: LIFECYCLE_ACTIVE,
            b: LIFECYCLE_EXPIRED,
            c: LIFECYCLE_LEGACY,
        }