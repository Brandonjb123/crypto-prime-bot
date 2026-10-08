"""Tests untuk TursoSignalLifecycleRepository — SQLite in-memory."""

import sqlite3
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from pydantic import ValidationError

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
    status          TEXT NOT NULL CHECK (status IN ('ACTIVE', 'EXPIRED')),
    expire_reason   TEXT CHECK (expire_reason IN ('TIME', 'SUPERSEDED')),
    created_at      TEXT NOT NULL,
    expires_at      TEXT NOT NULL,
    zone_low        REAL NOT NULL,
    zone_high       REAL NOT NULL,
    terminal_at     TEXT
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_signal_lifecycle_active_per_symbol
    ON signal_lifecycle(symbol) WHERE status = 'ACTIVE';
CREATE INDEX IF NOT EXISTS idx_signal_lifecycle_symbol_created
    ON signal_lifecycle(symbol, created_at DESC);
"""


class _SqliteResult:
    def __init__(self, columns, rows):
        self.columns = columns
        self.rows = rows


class _SqliteWrapper:
    """Adapter yang meniru TursoClient: execute() + batch() atomic."""

    def __init__(self, conn):
        self._conn = conn

    def execute(self, sql, params=None):
        cursor = self._conn.execute(sql, params or [])
        rows = cursor.fetchall()
        columns = [d[0] for d in cursor.description] if cursor.description else []
        return _SqliteResult(columns, rows)

    def batch(self, stmts):
        """Mimic libsql_client batch() — BEGIN/COMMIT/ROLLBACK."""
        results = []
        self._conn.execute("BEGIN")
        try:
            for stmt in stmts:
                if isinstance(stmt, tuple):
                    sql, params = stmt
                else:
                    sql, params = stmt, []
                cursor = self._conn.execute(sql, params or [])
                rows = cursor.fetchall()
                columns = (
                    [d[0] for d in cursor.description]
                    if cursor.description
                    else []
                )
                results.append(_SqliteResult(columns, rows))
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise
        return results


@pytest.fixture
def repo():
    # isolation_level=None → autocommit mode → explicit BEGIN/COMMIT works
    conn = sqlite3.connect(":memory:", isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    yield TursoSignalLifecycleRepository(_SqliteWrapper(conn))
    conn.close()


def _make_lifecycle(
    symbol="BTC",
    status=SignalLifecycleStatus.ACTIVE,
    expire_reason=None,
    created_offset_seconds=0,
    expires_offset_seconds=3600,
    zone_low=79000.0,
    zone_high=79400.0,
    terminal_at=None,
):
    now = datetime.now(UTC)
    return SignalLifecycle(
        signal_id=uuid4(),
        symbol=symbol,
        status=status,
        expire_reason=expire_reason,
        created_at=now + timedelta(seconds=created_offset_seconds),
        expires_at=now + timedelta(seconds=expires_offset_seconds),
        zone_low=zone_low,
        zone_high=zone_high,
        terminal_at=terminal_at,
    )


class TestSignalLifecycleModel:
    def test_create_active_with_required_fields(self):
        lc = _make_lifecycle()
        assert lc.status == SignalLifecycleStatus.ACTIVE
        assert lc.expire_reason is None
        assert lc.terminal_at is None

    def test_active_has_no_expire_reason(self):
        lc = _make_lifecycle()
        assert lc.expire_reason is None

    def test_active_has_no_terminal_at(self):
        lc = _make_lifecycle()
        assert lc.terminal_at is None

    def test_expired_supports_time_reason(self):
        lc = _make_lifecycle(
            status=SignalLifecycleStatus.EXPIRED,
            expire_reason=SignalLifecycleExpireReason.TIME,
            terminal_at=datetime.now(UTC),
        )
        assert lc.status == SignalLifecycleStatus.EXPIRED
        assert lc.expire_reason == SignalLifecycleExpireReason.TIME

    def test_expired_supports_superseded_reason(self):
        lc = _make_lifecycle(
            status=SignalLifecycleStatus.EXPIRED,
            expire_reason=SignalLifecycleExpireReason.SUPERSEDED,
            terminal_at=datetime.now(UTC),
        )
        assert lc.expire_reason == SignalLifecycleExpireReason.SUPERSEDED

    def test_immutable(self):
        lc = _make_lifecycle()
        with pytest.raises(ValidationError):
            lc.status = SignalLifecycleStatus.EXPIRED  # type: ignore


class TestGetActiveBySymbol:
    def test_returns_active_lifecycle(self, repo):
        lc = _make_lifecycle(symbol="BTC")
        repo.create_with_supersede(lc)

        found = repo.get_active_by_symbol("BTC")
        assert found is not None
        assert found.signal_id == lc.signal_id
        assert found.status == SignalLifecycleStatus.ACTIVE

    def test_returns_none_when_no_active(self, repo):
        assert repo.get_active_by_symbol("BTC") is None

    def test_returns_none_when_only_expired(self, repo):
        lc = _make_lifecycle(
            symbol="BTC",
            status=SignalLifecycleStatus.EXPIRED,
            expire_reason=SignalLifecycleExpireReason.TIME,
            terminal_at=datetime.now(UTC),
        )
        # Insert as EXPIRED directly via batch (create_with_supersede
        # only inserts ACTIVE)
        repo.client.batch([
            (
                "INSERT INTO signal_lifecycle (signal_id, symbol, status, "
                "expire_reason, created_at, expires_at, zone_low, zone_high, "
                "terminal_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    str(lc.signal_id), lc.symbol, lc.status.value,
                    lc.expire_reason.value, lc.created_at.isoformat(),
                    lc.expires_at.isoformat(), lc.zone_low, lc.zone_high,
                    lc.terminal_at.isoformat(),
                ],
            ),
        ])
        assert repo.get_active_by_symbol("BTC") is None


class TestCreateWithSupersede:
    def test_first_insert_no_supersede(self, repo):
        lc = _make_lifecycle(symbol="BTC")
        repo.create_with_supersede(lc)

        found = repo.get_active_by_symbol("BTC")
        assert found is not None
        assert found.signal_id == lc.signal_id

    def test_supersede_expires_previous_active(self, repo):
        old = _make_lifecycle(symbol="BTC", created_offset_seconds=-100)
        repo.create_with_supersede(old)

        new = _make_lifecycle(symbol="BTC", created_offset_seconds=0)
        repo.create_with_supersede(new)

        active = repo.get_active_by_symbol("BTC")
        assert active is not None
        assert active.signal_id == new.signal_id

    def test_previous_lifecycle_marked_expired_superseded(self, repo):
        old = _make_lifecycle(symbol="BTC", created_offset_seconds=-100)
        repo.create_with_supersede(old)

        new = _make_lifecycle(symbol="BTC", created_offset_seconds=0)
        repo.create_with_supersede(new)

        # Query old row directly
        result = repo.client.execute(
            "SELECT * FROM signal_lifecycle WHERE signal_id = ?",
            [str(old.signal_id)],
        )
        row = dict(zip(result.columns, result.rows[0], strict=False))
        assert row["status"] == SignalLifecycleStatus.EXPIRED.value
        assert row["expire_reason"] == SignalLifecycleExpireReason.SUPERSEDED.value
        assert row["terminal_at"] is not None

    def test_new_lifecycle_preserves_own_expires_at(self, repo):
        old = _make_lifecycle(symbol="BTC", created_offset_seconds=-100)
        repo.create_with_supersede(old)

        new = _make_lifecycle(
            symbol="BTC",
            created_offset_seconds=0,
            expires_offset_seconds=7200,
        )
        repo.create_with_supersede(new)

        # Old lifecycle's expires_at must be unchanged after supersede
        result = repo.client.execute(
            "SELECT * FROM signal_lifecycle WHERE signal_id = ?",
            [str(old.signal_id)],
        )
        row = dict(zip(result.columns, result.rows[0], strict=False))
        # old was created at now-100s, expires at now+3600s
        # store expect iso string unchanged
        assert row["expires_at"] == old.expires_at.isoformat()

        # New lifecycle has its own expires_at
        result2 = repo.client.execute(
            "SELECT * FROM signal_lifecycle WHERE signal_id = ?",
            [str(new.signal_id)],
        )
        row2 = dict(zip(result2.columns, result2.rows[0], strict=False))
        assert row2["expires_at"] == new.expires_at.isoformat()

    def test_different_symbol_does_not_supersede(self, repo):
        btc = _make_lifecycle(symbol="BTC")
        repo.create_with_supersede(btc)

        eth = _make_lifecycle(symbol="ETH")
        repo.create_with_supersede(eth)

        assert repo.get_active_by_symbol("BTC").signal_id == btc.signal_id
        assert repo.get_active_by_symbol("ETH").signal_id == eth.signal_id

    def test_duplicate_signal_id_rejected(self, repo):
        lc = _make_lifecycle(symbol="BTC")
        repo.create_with_supersede(lc)

        # Same signal_id again → PK conflict → batch rollback
        duplicate = SignalLifecycle(
            signal_id=lc.signal_id,
            symbol="ETH",
            status=SignalLifecycleStatus.ACTIVE,
            created_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(seconds=3600),
            zone_low=100.0,
            zone_high=110.0,
        )
        with pytest.raises(sqlite3.IntegrityError):
            repo.create_with_supersede(duplicate)

        # Original BTC still ACTIVE, ETH not created
        assert repo.get_active_by_symbol("BTC") is not None
        assert repo.get_active_by_symbol("ETH") is None


class TestAtomicity:
    def test_supersede_atomic_on_insert_conflict(self, repo):
        """Kalau INSERT conflict, UPDATE supersede tidak boleh committed."""
        old = _make_lifecycle(symbol="BTC", created_offset_seconds=-100)
        repo.create_with_supersede(old)

        # Craft new lifecycle with duplicate signal_id of old → INSERT PK conflict
        bad_new = SignalLifecycle(
            signal_id=old.signal_id,  # duplicate!
            symbol="BTC",
            status=SignalLifecycleStatus.ACTIVE,
            created_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(seconds=3600),
            zone_low=79000.0,
            zone_high=79400.0,
        )
        with pytest.raises(sqlite3.IntegrityError):
            repo.create_with_supersede(bad_new)

        # Old should STILL be ACTIVE (UPDATE must roll back)
        active = repo.get_active_by_symbol("BTC")
        assert active is not None
        assert active.signal_id == old.signal_id
        assert active.status == SignalLifecycleStatus.ACTIVE

    def test_db_enforces_unique_active_per_symbol(self, repo):
        """Partial unique index harus reject dua ACTIVE untuk symbol sama."""
        lc1 = _make_lifecycle(symbol="BTC")
        repo.create_with_supersede(lc1)

        # Bypass create_with_supersede → direct batch insert ACTIVE for BTC
        lc2 = _make_lifecycle(symbol="BTC", created_offset_seconds=10)
        with pytest.raises(sqlite3.IntegrityError):
            repo.client.batch([
                (
                    "INSERT INTO signal_lifecycle (signal_id, symbol, status, "
                    "expire_reason, created_at, expires_at, zone_low, zone_high, "
                    "terminal_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    [
                        str(lc2.signal_id), lc2.symbol, lc2.status.value,
                        None, lc2.created_at.isoformat(),
                        lc2.expires_at.isoformat(), lc2.zone_low, lc2.zone_high,
                        None,
                    ],
                ),
            ])


class TestMarkExpired:
    def test_mark_expired_time(self, repo):
        lc = _make_lifecycle(symbol="BTC")
        repo.create_with_supersede(lc)

        repo.mark_expired(lc.signal_id, SignalLifecycleExpireReason.TIME)

        assert repo.get_active_by_symbol("BTC") is None

        result = repo.client.execute(
            "SELECT * FROM signal_lifecycle WHERE signal_id = ?",
            [str(lc.signal_id)],
        )
        row = dict(zip(result.columns, result.rows[0], strict=False))
        assert row["status"] == SignalLifecycleStatus.EXPIRED.value
        assert row["expire_reason"] == SignalLifecycleExpireReason.TIME.value
        assert row["terminal_at"] is not None

    def test_mark_expired_nonexistent_is_noop(self, repo):
        # Signal tidak ada → UPDATE tidak match, tidak raise
        repo.mark_expired(uuid4(), SignalLifecycleExpireReason.TIME)


class TestGetAllActive:
    def test_get_all_active_returns_active_only(self, repo):
        active1 = _make_lifecycle(symbol="BTC")
        active2 = _make_lifecycle(symbol="ETH")
        repo.create_with_supersede(active1)
        repo.create_with_supersede(active2)

        result = repo.get_all_active()
        assert len(result) == 2
        symbols = {lc.symbol for lc in result}
        assert symbols == {"BTC", "ETH"}

    def test_get_all_active_empty(self, repo):
        assert repo.get_all_active() == []

    def test_superseded_lifecycle_not_in_active(self, repo):
        old = _make_lifecycle(symbol="BTC", created_offset_seconds=-100)
        repo.create_with_supersede(old)
        new = _make_lifecycle(symbol="BTC", created_offset_seconds=0)
        repo.create_with_supersede(new)

        result = repo.get_all_active()
        assert len(result) == 1
        assert result[0].signal_id == new.signal_id

    def test_expired_lifecycle_not_in_active(self, repo):
        lc = _make_lifecycle(symbol="BTC")
        repo.create_with_supersede(lc)
        repo.mark_expired(lc.signal_id, SignalLifecycleExpireReason.TIME)

        assert repo.get_all_active() == []
