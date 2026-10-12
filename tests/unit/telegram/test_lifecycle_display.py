"""Unit tests untuk resolve_lifecycle_states (H3.2 R2)."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from src.core.models.lifecycle_lookup import (
    LifecycleLookupResult,
    LifecycleRecord,
)
from src.telegram.lifecycle_display import (
    LIFECYCLE_ACTIVE,
    LIFECYCLE_EPOCH_UTC,
    LIFECYCLE_EXPIRED,
    LIFECYCLE_LEGACY,
    LIFECYCLE_RECENT,
    LIFECYCLE_UNKNOWN,
    resolve_lifecycle_states,
)


class _StubLifecycleRepo:
    def __init__(self, found=None, failed=None, raises=None):
        self.found = found or {}
        self.failed = failed or set()
        self.raises = raises

    def get_lifecycle_lookup(self, signal_ids):
        if self.raises is not None:
            raise self.raises
        found = {sid: self.found[sid] for sid in signal_ids if sid in self.found}
        absent = {sid for sid in signal_ids if sid not in self.found and sid not in self.failed}
        failed = {sid for sid in signal_ids if sid in self.failed}
        return LifecycleLookupResult(found=found, absent=absent, failed=failed)


class _Sig:
    def __init__(self, signal_id=None, status="ACTIVE", created_at=None):
        self.signal_id = signal_id or uuid4()
        self.status = status
        self.created_at = created_at


NOW = datetime(2026, 10, 11, 8, 0, 0, tzinfo=UTC)


class TestResolveLifecycleStates:
    def test_empty_input(self):
        repo = _StubLifecycleRepo()
        assert resolve_lifecycle_states(repo, [], NOW) == {}

    def test_active(self):
        sid = uuid4()
        sig = _Sig(sid, created_at=NOW)
        repo = _StubLifecycleRepo(
            found={sid: LifecycleRecord(sid, "ACTIVE", NOW + timedelta(hours=1))}
        )
        assert resolve_lifecycle_states(repo, [sig], NOW) == {sid: LIFECYCLE_ACTIVE}

    def test_active_past_expires_becomes_expired(self):
        sid = uuid4()
        sig = _Sig(sid, created_at=NOW)
        repo = _StubLifecycleRepo(
            found={sid: LifecycleRecord(sid, "ACTIVE", NOW - timedelta(hours=1))}
        )
        assert resolve_lifecycle_states(repo, [sig], NOW) == {sid: LIFECYCLE_EXPIRED}

    def test_active_with_no_expires_becomes_unknown(self):
        """B1: ACTIVE record without expires_at → UNKNOWN (defensive)."""
        sid = uuid4()
        sig = _Sig(sid, created_at=NOW)
        repo = _StubLifecycleRepo(
            found={sid: LifecycleRecord(sid, "ACTIVE", None)}
        )
        assert resolve_lifecycle_states(repo, [sig], NOW) == {
            sid: LIFECYCLE_UNKNOWN
        }

    def test_active_with_naive_expires_becomes_unknown(self):
        """R1: naive expires_at cannot safely be compared."""
        sid = uuid4()
        sig = _Sig(sid, created_at=NOW)
        naive_expires = datetime(2026, 10, 12, 0, 0, 0)  # naive
        repo = _StubLifecycleRepo(
            found={sid: LifecycleRecord(sid, "ACTIVE", naive_expires)}
        )
        assert resolve_lifecycle_states(repo, [sig], NOW) == {sid: LIFECYCLE_UNKNOWN}

    def test_expired(self):
        sid = uuid4()
        sig = _Sig(sid, created_at=NOW)
        repo = _StubLifecycleRepo(found={sid: LifecycleRecord(sid, "EXPIRED", None)})
        assert resolve_lifecycle_states(repo, [sig], NOW) == {sid: LIFECYCLE_EXPIRED}

    def test_absent_pre_epoch_aware_becomes_legacy(self):
        sid = uuid4()
        sig = _Sig(sid, created_at=LIFECYCLE_EPOCH_UTC - timedelta(days=1))
        repo = _StubLifecycleRepo()
        assert resolve_lifecycle_states(repo, [sig], NOW) == {sid: LIFECYCLE_LEGACY}

    def test_absent_post_epoch_aware_becomes_recent(self):
        sid = uuid4()
        sig = _Sig(sid, created_at=LIFECYCLE_EPOCH_UTC + timedelta(hours=1))
        repo = _StubLifecycleRepo()
        assert resolve_lifecycle_states(repo, [sig], NOW) == {sid: LIFECYCLE_RECENT}

    def test_naive_created_at_becomes_unknown(self):
        """R1: naive created_at cannot prove pre-epoch → UNKNOWN (not LEGACY)."""
        sid = uuid4()
        sig = _Sig(sid, created_at=datetime(2026, 10, 1, 0, 0, 0))  # naive
        repo = _StubLifecycleRepo()
        assert resolve_lifecycle_states(repo, [sig], NOW) == {sid: LIFECYCLE_UNKNOWN}

    def test_missing_created_at_becomes_unknown(self):
        sid = uuid4()
        sig = _Sig(sid, created_at=None)
        repo = _StubLifecycleRepo()
        assert resolve_lifecycle_states(repo, [sig], NOW) == {sid: LIFECYCLE_UNKNOWN}

    def test_query_failure_becomes_unknown(self):
        sid = uuid4()
        sig = _Sig(sid, created_at=NOW)
        repo = _StubLifecycleRepo(raises=RuntimeError("db down"))
        assert resolve_lifecycle_states(repo, [sig], NOW) == {sid: LIFECYCLE_UNKNOWN}

    def test_failed_bucket_becomes_unknown(self):
        """R3: failed must not be disguised as absent."""
        sid = uuid4()
        sig = _Sig(sid, created_at=LIFECYCLE_EPOCH_UTC - timedelta(days=1))
        repo = _StubLifecycleRepo(failed={sid})
        assert resolve_lifecycle_states(repo, [sig], NOW) == {sid: LIFECYCLE_UNKNOWN}

    def test_unrecognized_state_becomes_unknown(self):
        sid = uuid4()
        sig = _Sig(sid, created_at=NOW)
        repo = _StubLifecycleRepo(found={sid: LifecycleRecord(sid, "WEIRD", None)})
        assert resolve_lifecycle_states(repo, [sig], NOW) == {sid: LIFECYCLE_UNKNOWN}

    def test_dedup_input(self):
        sid = uuid4()
        sig = _Sig(sid, created_at=NOW)
        repo = _StubLifecycleRepo(
            found={sid: LifecycleRecord(sid, "ACTIVE", NOW + timedelta(hours=1))}
        )
        assert resolve_lifecycle_states(repo, [sig, sig, sig], NOW) == {
            sid: LIFECYCLE_ACTIVE
        }

    def test_skipped_signals_are_skipped(self):
        sid = uuid4()
        sig = _Sig(sid, status="SKIPPED", created_at=NOW)
        repo = _StubLifecycleRepo(found={sid: LifecycleRecord(sid, "ACTIVE", None)})
        assert resolve_lifecycle_states(repo, [sig], NOW) == {}

    def test_invalid_signals_are_skipped(self):
        sid = uuid4()
        sig = _Sig(sid, status="INVALID", created_at=NOW)
        repo = _StubLifecycleRepo(found={sid: LifecycleRecord(sid, "ACTIVE", None)})
        assert resolve_lifecycle_states(repo, [sig], NOW) == {}

    def test_naive_now_utc_returns_empty(self):
        sid = uuid4()
        sig = _Sig(sid, created_at=NOW)
        repo = _StubLifecycleRepo()
        naive_now = datetime(2026, 10, 11, 8, 0, 0)
        assert resolve_lifecycle_states(repo, [sig], naive_now) == {}

    def test_mixed_states(self):
        s_active = _Sig(created_at=NOW)
        s_expired = _Sig(created_at=NOW)
        s_legacy = _Sig(created_at=LIFECYCLE_EPOCH_UTC - timedelta(days=1))
        s_recent = _Sig(created_at=LIFECYCLE_EPOCH_UTC + timedelta(hours=1))
        s_failed = _Sig(created_at=NOW)
        repo = _StubLifecycleRepo(
            found={
                s_active.signal_id: LifecycleRecord(
                    s_active.signal_id, "ACTIVE", NOW + timedelta(hours=1)
                ),
                s_expired.signal_id: LifecycleRecord(
                    s_expired.signal_id, "EXPIRED", None
                ),
            },
            failed={s_failed.signal_id},
        )
        result = resolve_lifecycle_states(
            repo, [s_active, s_expired, s_legacy, s_recent, s_failed], NOW
        )
        assert result == {
            s_active.signal_id: LIFECYCLE_ACTIVE,
            s_expired.signal_id: LIFECYCLE_EXPIRED,
            s_legacy.signal_id: LIFECYCLE_LEGACY,
            s_recent.signal_id: LIFECYCLE_RECENT,
            s_failed.signal_id: LIFECYCLE_UNKNOWN,
        }


class TestNoWriteInResolver:
    def test_only_get_lifecycle_lookup_is_called(self):
        sid = uuid4()
        sig = _Sig(sid, created_at=NOW)
        calls = []

        class _Recorder:
            def get_lifecycle_lookup(self, signal_ids):
                calls.append("get_lifecycle_lookup")
                return LifecycleLookupResult(absent=set(signal_ids))

            def append(self, *a, **kw):
                calls.append("append")
                raise AssertionError("append must not be called")

            def save(self, *a, **kw):
                calls.append("save")
                raise AssertionError("save must not be called")

            def execute(self, *a, **kw):
                calls.append("execute")
                raise AssertionError("execute must not be called")

        resolve_lifecycle_states(_Recorder(), [sig], NOW)
        assert calls == ["get_lifecycle_lookup"]


class TestFailedNeverBecomesLegacyOrRecent:
    """R4: failed bucket must map to UNKNOWN, not LEGACY/RECENT."""

    def test_failed_pre_epoch_signal_becomes_unknown_not_legacy(self):
        sid = uuid4()
        sig = _Sig(sid, created_at=LIFECYCLE_EPOCH_UTC - timedelta(days=1))
        repo = _StubLifecycleRepo(failed={sid})
        result = resolve_lifecycle_states(repo, [sig], NOW)
        assert result[sid] == LIFECYCLE_UNKNOWN
        assert result[sid] != LIFECYCLE_LEGACY

    def test_failed_post_epoch_signal_becomes_unknown_not_recent(self):
        sid = uuid4()
        sig = _Sig(sid, created_at=LIFECYCLE_EPOCH_UTC + timedelta(hours=1))
        repo = _StubLifecycleRepo(failed={sid})
        result = resolve_lifecycle_states(repo, [sig], NOW)
        assert result[sid] == LIFECYCLE_UNKNOWN
        assert result[sid] != LIFECYCLE_RECENT

    def test_failed_and_absent_mixed(self):
        s_failed = _Sig(created_at=LIFECYCLE_EPOCH_UTC - timedelta(days=1))
        s_absent = _Sig(created_at=LIFECYCLE_EPOCH_UTC - timedelta(days=1))
        repo = _StubLifecycleRepo(failed={s_failed.signal_id})
        result = resolve_lifecycle_states(repo, [s_failed, s_absent], NOW)
        assert result[s_failed.signal_id] == LIFECYCLE_UNKNOWN
        assert result[s_absent.signal_id] == LIFECYCLE_LEGACY


class TestReadOnlyPortDependency:
    """R7: resolver must work with a read-only protocol (no write methods)."""

    def test_read_only_protocol_works(self):
        sid = uuid4()
        sig = _Sig(sid, created_at=NOW)

        class _ReadOnly:
            """Only exposes get_lifecycle_lookup — no write methods."""

            def __init__(self, found):
                self._found = found

            def get_lifecycle_lookup(self, signal_ids):
                f = {i: self._found[i] for i in signal_ids if i in self._found}
                a = {i for i in signal_ids if i not in self._found}
                return LifecycleLookupResult(found=f, absent=a)

            def __getattr__(self, name):
                # If resolver tries to access anything else (e.g. mark_expired),
                # raise to prove dependency boundary.
                raise AssertionError(
                    f"resolver accessed unexpected attribute: {name}"
                )

        rec = LifecycleRecord(sid, "ACTIVE", NOW + timedelta(hours=1))
        repo = _ReadOnly({sid: rec})

        result = resolve_lifecycle_states(repo, [sig], NOW)
        assert result == {sid: LIFECYCLE_ACTIVE}

    def test_resolver_does_not_access_write_methods(self):
        sid = uuid4()
        sig = _Sig(sid, created_at=NOW)
        touched = []

        class _Probe:
            def get_lifecycle_lookup(self, signal_ids):
                return LifecycleLookupResult(absent=set(signal_ids))

            def mark_expired(self, *a, **kw):
                touched.append("mark_expired")
                raise AssertionError("mark_expired must not be touched")

            def create_with_supersede(self, *a, **kw):
                touched.append("create_with_supersede")
                raise AssertionError("create_with_supersede must not be touched")

            def __getattr__(self, name):
                touched.append(name)
                raise AssertionError(f"unexpected attribute access: {name}")

        resolve_lifecycle_states(_Probe(), [sig], NOW)
        assert "mark_expired" not in touched
        assert "create_with_supersede" not in touched


class TestEpochBoundaryStrictness:
    """B4: epoch comparison is strictly `<` LIFECYCLE_EPOCH_UTC."""

    def test_created_one_second_before_epoch_is_legacy(self):
        sid = uuid4()
        sig = _Sig(
            sid,
            created_at=LIFECYCLE_EPOCH_UTC - timedelta(seconds=1),
        )
        repo = _StubLifecycleRepo()
        assert resolve_lifecycle_states(repo, [sig], NOW) == {sid: LIFECYCLE_LEGACY}

    def test_created_exactly_at_epoch_is_recent(self):
        sid = uuid4()
        sig = _Sig(sid, created_at=LIFECYCLE_EPOCH_UTC)
        repo = _StubLifecycleRepo()
        assert resolve_lifecycle_states(repo, [sig], NOW) == {sid: LIFECYCLE_RECENT}

    def test_created_one_second_after_epoch_is_recent(self):
        sid = uuid4()
        sig = _Sig(
            sid,
            created_at=LIFECYCLE_EPOCH_UTC + timedelta(seconds=1),
        )
        repo = _StubLifecycleRepo()
        assert resolve_lifecycle_states(repo, [sig], NOW) == {sid: LIFECYCLE_RECENT}

    def test_created_one_second_before_epoch_with_non_utc_offset(self):
        """Aware non-UTC datetime with equivalent UTC instant must classify correctly."""
        from datetime import timedelta as _td
        from datetime import timezone

        # Same instant as (LIFECYCLE_EPOCH - 1s), expressed in +07:00
        utc_instant = LIFECYCLE_EPOCH_UTC - timedelta(seconds=1)
        non_utc_tz = timezone(_td(hours=7))
        sig = _Sig(uuid4(), created_at=utc_instant.astimezone(non_utc_tz))
        repo = _StubLifecycleRepo()
        assert resolve_lifecycle_states(repo, [sig], NOW) == {
            sig.signal_id: LIFECYCLE_LEGACY
        }

    def test_created_at_epoch_with_non_utc_offset_is_recent(self):
        from datetime import timedelta as _td
        from datetime import timezone

        non_utc_tz = timezone(_td(hours=-5))
        sig = _Sig(uuid4(), created_at=LIFECYCLE_EPOCH_UTC.astimezone(non_utc_tz))
        repo = _StubLifecycleRepo()
        assert resolve_lifecycle_states(repo, [sig], NOW) == {
            sig.signal_id: LIFECYCLE_RECENT
        }