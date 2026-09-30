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
    CREATE TABLE IF NOT EXISTS positions (
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
    CREATE INDEX IF NOT EXISTS idx_positions_status
    ON positions(status)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_positions_symbol_status
    ON positions(symbol, status)
    """,
]


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

    print("Migration complete.")
    client.close()


if __name__ == "__main__":
    main()