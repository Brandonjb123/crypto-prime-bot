"""Migration script — buat tabel V2 di Turso. Idempotent.

Usage:
    python scripts/migrate_db.py
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config.settings import settings  # noqa: E402
from src.storage.adapters.turso_client import TursoClient  # noqa: E402

SCHEMA_SQL = [
    """
    CREATE TABLE IF NOT EXISTS trading_signals (
        signal_id       TEXT PRIMARY KEY,
        symbol          TEXT NOT NULL,
        side            TEXT NOT NULL,
        status          TEXT NOT NULL,
        entry_price     REAL,
        stop_loss       REAL,
        take_profit     REAL,
        take_profit_1   REAL,
        take_profit_2   REAL,
        position_size   REAL NOT NULL DEFAULT 0.0,
        risk_percent    REAL NOT NULL DEFAULT 0.0,
        confidence      INTEGER NOT NULL DEFAULT 0,
        risk_level      TEXT NOT NULL DEFAULT 'MEDIUM',
        reasoning       TEXT,
        created_at      TEXT NOT NULL
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_signals_symbol_created
    ON trading_signals(symbol, created_at DESC)
    """,
    """
    CREATE TABLE IF NOT EXISTS trading_positions (
        position_id     TEXT PRIMARY KEY,
        execution_id    TEXT NOT NULL,
        order_id        TEXT NOT NULL,
        signal_id       TEXT REFERENCES trading_signals(signal_id),
        symbol          TEXT NOT NULL,
        side            TEXT NOT NULL,
        status          TEXT NOT NULL,
        entry_price     REAL NOT NULL,
        stop_loss       REAL NOT NULL,
        take_profit     REAL NOT NULL,
        tp1_price       REAL,
        tp2_price       REAL,
        position_size   REAL NOT NULL,
        opened_at       TEXT NOT NULL,
        closed_at       TEXT,
        close_reason    TEXT,
        last_price      REAL,
        last_updated    TEXT,
        realized_pnl    REAL NOT NULL DEFAULT 0.0
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_trading_positions_status
    ON trading_positions(status)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_trading_positions_symbol_status
    ON trading_positions(symbol, status)
    """,
    """
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
    )
    """,
    """
    CREATE UNIQUE INDEX IF NOT EXISTS idx_signal_lifecycle_active_per_symbol
    ON signal_lifecycle(symbol)
    WHERE status = 'ACTIVE'
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_signal_lifecycle_symbol_created
    ON signal_lifecycle(symbol, created_at DESC)
    """,
    """
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
    )
    """,
    """
    CREATE UNIQUE INDEX IF NOT EXISTS idx_notification_outbox_unique_event
    ON notification_outbox(signal_id, event_type, telegram_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_notification_outbox_due
    ON notification_outbox(status, next_retry_at)
    """,
]


def _column_exists(client: TursoClient, table: str, column: str) -> bool:
    """Check if column exists via PRAGMA. SQLite has no ADD COLUMN IF NOT EXISTS."""
    result = client.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in result.rows)


def main() -> None:
    print("Connecting to Turso...")
    client = TursoClient(
        url=settings.TURSO_DATABASE_URL,
        auth_token=settings.TURSO_AUTH_TOKEN,
    )
    client.connect()
    print("Connected.")

    for i, sql in enumerate(SCHEMA_SQL, 1):
        print(f"Applying schema step {i}/{len(SCHEMA_SQL)}...")
        client.execute(sql)

    # C0.0.4A: guarded ALTER TABLE signal_lifecycle
    if not _column_exists(client, "signal_lifecycle", "superseded_by_signal_id"):
        print("Applying guarded migration: ADD COLUMN superseded_by_signal_id...")
        client.execute(
            "ALTER TABLE signal_lifecycle "
            "ADD COLUMN superseded_by_signal_id TEXT"
        )
        print("  applied")
    else:
        print("Guarded migration: superseded_by_signal_id already exists — skip")

    print("Migration complete.")
    client.close()


if __name__ == "__main__":
    main()