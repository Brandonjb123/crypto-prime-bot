import sqlite3
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from src.core.models.notification_outbox import (
    OutboxEventType,
    OutboxStatus,
)
from src.storage.adapters.turso_notification_outbox_repository import (
    TursoNotificationOutboxRepository,
)

SCHEMA = """
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
        self._conn.commit()
        return _SqliteResult(cols, rows)


@pytest.fixture
def repo():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    yield TursoNotificationOutboxRepository(_SqliteWrapper(conn))
    conn.close()


def _insert(wrapper, *, event_type=OutboxEventType.NEW_SIGNAL,
            signal_id=None, telegram_id=100, status=OutboxStatus.PENDING):
    now = datetime.now(UTC).isoformat()
    wrapper.execute(
        "INSERT INTO notification_outbox "
        "(signal_id, event_type, telegram_id, status, attempts, "
        " created_at, updated_at) "
        "VALUES (?, ?, ?, ?, 0, ?, ?)",
        [
            str(signal_id or uuid4()),
            event_type.value,
            telegram_id,
            status.value,
            now,
            now,
        ],
    )


class TestGetPending:
    def test_empty(self, repo):
        assert repo.get_pending() == []
        assert repo.count_pending() == 0

    def test_returns_pending_only(self, repo):
        wrapper = repo.client
        _insert(wrapper, status=OutboxStatus.PENDING, telegram_id=1)
        _insert(wrapper, status=OutboxStatus.SENT, telegram_id=2)
        pending = repo.get_pending()
        assert len(pending) == 1
        assert pending[0].telegram_id == 1
        assert pending[0].status == OutboxStatus.PENDING
        assert repo.count_pending() == 1

    def test_limit(self, repo):
        wrapper = repo.client
        for i in range(5):
            _insert(wrapper, telegram_id=i)
        assert len(repo.get_pending(limit=2)) == 2

    def test_defaults_applied(self, repo):
        wrapper = repo.client
        _insert(wrapper, telegram_id=42)
        pending = repo.get_pending()
        assert pending[0].attempts == 0
        assert pending[0].sent_at is None
        assert pending[0].message_id is None
        assert pending[0].last_error is None
        assert pending[0].next_retry_at is None


class TestUniqueConstraint:
    def test_duplicate_event_rejected(self, repo):
        wrapper = repo.client
        sig = uuid4()
        _insert(wrapper, signal_id=sig, telegram_id=1)
        with pytest.raises(sqlite3.IntegrityError):
            _insert(wrapper, signal_id=sig, telegram_id=1)

    def test_same_signal_different_recipient_ok(self, repo):
        wrapper = repo.client
        sig = uuid4()
        _insert(wrapper, signal_id=sig, telegram_id=1)
        _insert(wrapper, signal_id=sig, telegram_id=2)
        assert repo.count_pending() == 2

    def test_same_signal_different_event_ok(self, repo):
        wrapper = repo.client
        sig = uuid4()
        _insert(wrapper, signal_id=sig, telegram_id=1,
                event_type=OutboxEventType.NEW_SIGNAL)
        _insert(wrapper, signal_id=sig, telegram_id=1,
                event_type=OutboxEventType.EXPIRY)
        assert repo.count_pending() == 2


class TestModelDeserialization:
    def test_full_row_roundtrip(self, repo):
        wrapper = repo.client
        sig = uuid4()
        now = datetime.now(UTC).isoformat()
        wrapper.execute(
            "INSERT INTO notification_outbox "
            "(signal_id, event_type, telegram_id, status, attempts, "
            " sent_at, message_id, last_error, next_retry_at, "
            " created_at, updated_at) "
            "VALUES (?, 'NEW_SIGNAL', 555, 'SENT', 2, ?, 999, 'boom', ?, ?, ?)",
            [str(sig), now, now, now, now],
        )
        # get_pending hanya PENDING — jadi query langsung
        r = wrapper.execute("SELECT * FROM notification_outbox")
        rows = [dict(zip(r.columns, row, strict=False)) for row in r.rows]
        obj = repo._row_to_outbox(rows[0])
        assert obj.telegram_id == 555
        assert obj.status == OutboxStatus.SENT
        assert obj.attempts == 2
        assert obj.message_id == 999
        assert obj.last_error == "boom"