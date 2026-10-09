"""C0.0.4A — Lifecycle repository outbox integration (flag ON/OFF)."""

import sqlite3
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from src.core.models.signal_lifecycle import SignalLifecycle
from src.core.types.enums import (
    SignalLifecycleExpireReason,
    SignalLifecycleStatus,
)
from src.storage.adapters.turso_signal_lifecycle_repository import (
    TursoSignalLifecycleRepository,
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS signal_lifecycle (
    signal_id       TEXT PRIMARY KEY,
    symbol          TEXT NOT NULL,
    status          TEXT NOT NULL CHECK (status IN ('ACTIVE','EXPIRED')),
    expire_reason   TEXT CHECK (expire_reason IN ('TIME','SUPERSEDED')),
    created_at      TEXT NOT NULL,
    expires_at      TEXT NOT NULL,
    zone_low        REAL NOT NULL,
    zone_high       REAL NOT NULL,
    terminal_at     TEXT,
    superseded_by_signal_id TEXT
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_active_per_symbol
    ON signal_lifecycle(symbol) WHERE status='ACTIVE';

CREATE TABLE IF NOT EXISTS notification_outbox (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    signal_id       TEXT NOT NULL,
    event_type      TEXT NOT NULL,
    telegram_id     INTEGER NOT NULL,
    status          TEXT NOT NULL DEFAULT 'PENDING',
    attempts        INTEGER NOT NULL DEFAULT 0,
    sent_at         TEXT NULL,
    message_id      INTEGER NULL,
    last_error      TEXT NULL,
    next_retry_at   TEXT NULL,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_outbox_unique_event
    ON notification_outbox(signal_id, event_type, telegram_id);
"""


class _SqliteResult:
    def __init__(self, columns, rows):
        self.columns = columns
        self.rows = rows


class _SqliteWrapper:
    def __init__(self, conn):
        self._conn = conn

    def execute(self, sql, params=None):
        cur = self._conn.execute(sql, params or [])
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description] if cur.description else []
        return _SqliteResult(cols, rows)

    def batch(self, stmts):
        results = []
        self._conn.execute("BEGIN")
        try:
            for stmt in stmts:
                sql, params = stmt if isinstance(stmt, tuple) else (stmt, [])
                cur = self._conn.execute(sql, params or [])
                rows = cur.fetchall()
                cols = [d[0] for d in cur.description] if cur.description else []
                results.append(_SqliteResult(cols, rows))
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise
        return results


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:", isolation_level=None)
    c.row_factory = sqlite3.Row
    c.executescript(SCHEMA)
    yield c
    c.close()


def _make_lifecycle(symbol="BTC", offset_seconds=0):
    now = datetime.now(UTC)
    return SignalLifecycle(
        signal_id=uuid4(),
        symbol=symbol,
        status=SignalLifecycleStatus.ACTIVE,
        created_at=now + timedelta(seconds=offset_seconds),
        expires_at=now + timedelta(seconds=3600),
        zone_low=100.0,
        zone_high=110.0,
    )


def _count_outbox(wrapper, event_type=None):
    if event_type:
        r = wrapper.execute(
            "SELECT COUNT(*) FROM notification_outbox WHERE event_type=?",
            [event_type],
        )
    else:
        r = wrapper.execute("SELECT COUNT(*) FROM notification_outbox")
    return r.rows[0][0]


class TestFlagOFF:
    def test_supersede_flag_off_no_outbox(self, conn):
        w = _SqliteWrapper(conn)
        repo = TursoSignalLifecycleRepository(
            w, outbox_enabled=False, recipient_ids=[]
        )
        old = _make_lifecycle(offset_seconds=-100)
        repo.create_with_supersede(old)
        new = _make_lifecycle(offset_seconds=0)
        repo.create_with_supersede(new)
        # superseded_by populated regardless of flag
        r = w.execute(
            "SELECT superseded_by_signal_id FROM signal_lifecycle "
            "WHERE signal_id=?",
            [str(old.signal_id)],
        )
        assert r.rows[0][0] == str(new.signal_id)
        assert _count_outbox(w) == 0


class TestFlagON:
    def test_supersede_flag_on_enqueues_replacement_and_new_signal(self, conn):
        w = _SqliteWrapper(conn)
        repo = TursoSignalLifecycleRepository(
            w, outbox_enabled=True, recipient_ids=["100", "200"]
        )
        # First signal → NEW_SIGNAL x2
        old = _make_lifecycle(offset_seconds=-100)
        repo.create_with_supersede(old)
        assert _count_outbox(w, "NEW_SIGNAL") == 2
        # Supersede → REPLACEMENT x2 + NEW_SIGNAL x2
        new = _make_lifecycle(offset_seconds=0)
        repo.create_with_supersede(new)
        assert _count_outbox(w, "REPLACEMENT") == 2
        assert _count_outbox(w, "NEW_SIGNAL") == 4
        # Verify telegram_id int + default fields
        r = w.execute(
            "SELECT telegram_id, status, attempts, sent_at, message_id, "
            "       last_error, next_retry_at "
            "FROM notification_outbox WHERE event_type='REPLACEMENT' "
            "ORDER BY telegram_id"
        )
        for row in r.rows:
            assert isinstance(row[0], int)
            assert row[0] in (100, 200)
            assert row[1] == "PENDING"
            assert row[2] == 0
            assert row[3] is None
            assert row[4] is None
            assert row[5] is None
            assert row[6] is None

    def test_mark_expired_time_flag_on_enqueues_expiry(self, conn):
        w = _SqliteWrapper(conn)
        repo = TursoSignalLifecycleRepository(
            w, outbox_enabled=True, recipient_ids=["100"]
        )
        lc = _make_lifecycle()
        repo.create_with_supersede(lc)
        assert _count_outbox(w, "NEW_SIGNAL") == 1
        repo.mark_expired(lc.signal_id, SignalLifecycleExpireReason.TIME)
        assert _count_outbox(w, "EXPIRY") == 1

    def test_mark_expired_superseded_reason_no_expiry(self, conn):
        w = _SqliteWrapper(conn)
        repo = TursoSignalLifecycleRepository(
            w, outbox_enabled=True, recipient_ids=["100"]
        )
        lc = _make_lifecycle()
        repo.create_with_supersede(lc)
        repo.mark_expired(lc.signal_id, SignalLifecycleExpireReason.SUPERSEDED)
        assert _count_outbox(w, "EXPIRY") == 0


class TestEnqueueIdempotency:
    def test_duplicate_supersede_same_new_signal_no_duplicate_outbox(self, conn):
        w = _SqliteWrapper(conn)
        repo = TursoSignalLifecycleRepository(
            w, outbox_enabled=True, recipient_ids=["100"]
        )
        old = _make_lifecycle(offset_seconds=-100)
        repo.create_with_supersede(old)
        new = _make_lifecycle(offset_seconds=0)
        repo.create_with_supersede(new)
        after_first = _count_outbox(w)
        # Re-enqueue NEW_SIGNAL for `new` manually via direct ON CONFLICT
        # (simulating duplicate pipeline trigger). Should be no-op.
        w.batch([
            (
                "INSERT INTO notification_outbox "
                "(signal_id, event_type, telegram_id, status, attempts, "
                " created_at, updated_at) "
                "VALUES (?, 'NEW_SIGNAL', ?, 'PENDING', 0, ?, ?) "
                "ON CONFLICT(signal_id, event_type, telegram_id) DO NOTHING",
                [
                    str(new.signal_id), 100,
                    datetime.now(UTC).isoformat(),
                    datetime.now(UTC).isoformat(),
                ],
            )
        ])
        assert _count_outbox(w) == after_first


class TestAtomicRollback:
    def test_supersede_rollback_on_failure(self, conn):
        """If INSERT new lifecycle fails, prior statements roll back."""
        w = _SqliteWrapper(conn)
        repo = TursoSignalLifecycleRepository(
            w, outbox_enabled=True, recipient_ids=["100"]
        )
        old = _make_lifecycle(offset_seconds=-100)
        repo.create_with_supersede(old)
        prev_outbox = _count_outbox(w)
        dup = SignalLifecycle(
            signal_id=old.signal_id,  # duplicate PK
            symbol="ETH",
            status=SignalLifecycleStatus.ACTIVE,
            created_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(seconds=3600),
            zone_low=1.0,
            zone_high=2.0,
        )
        with pytest.raises(sqlite3.IntegrityError):
            repo.create_with_supersede(dup)
        r = w.execute(
            "SELECT status FROM signal_lifecycle WHERE signal_id=?",
            [str(old.signal_id)],
        )
        assert r.rows[0][0] == "ACTIVE"
        assert _count_outbox(w) == prev_outbox