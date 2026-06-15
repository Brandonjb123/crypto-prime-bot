# db/database.py
import os
import sqlite3
from turso_python import TursoConnection

TURSO_URL = os.getenv("TURSO_DATABASE_URL")
TURSO_TOKEN = os.getenv("TURSO_AUTH_TOKEN")

_connection = None


class TursoCursor:
    """Membungkus hasil query Turso agar mirip sqlite3.Cursor."""
    def __init__(self, conn, rows=None, description=None):
        self._conn = conn
        self._rows = rows or []
        self.description = description
        self.rowcount = len(self._rows)
        self._index = 0

    def fetchone(self):
        if self._index < len(self._rows):
            row = self._rows[self._index]
            self._index += 1
            return row
        return None

    def fetchall(self):
        return self._rows[self._index:]

    def execute(self, sql, params=None):
        if params:
            for param in params:
                sql = sql.replace("?", repr(param), 1)
        result = self._conn._conn.execute_query(sql)
        # Debug: catat hasil query
        from loguru import logger
        logger.info(f"QUERY: {sql}")
        logger.info(f"RESULT: {result}")
        if isinstance(result, list):
            self._rows = result
        elif isinstance(result, dict) and "rows" in result:
            self._rows = result["rows"]
        else:
            self._rows = []
        self.description = None
        self.rowcount = len(self._rows)
        self._index = 0
        return self

    def close(self):
        pass


class TursoAdapter:
    """Adapter agar TursoConnection berperilaku seperti sqlite3.Connection."""
    def __init__(self, url, token):
        self._conn = TursoConnection(url, token)
        self.row_factory = None

    def cursor(self):
        return TursoCursor(self)

    def commit(self):
        pass  # Turso auto-commit

    def close(self):
        pass


def get_connection():
    global _connection
    if _connection is None:
        if TURSO_URL and TURSO_TOKEN:
            _connection = TursoAdapter(TURSO_URL, TURSO_TOKEN)
        else:
            DB_PATH = os.getenv("DB_PATH", "crypto_prime.db")
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            return conn
    return _connection


def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            chat_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            plan TEXT DEFAULT 'free'
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            pair TEXT NOT NULL,
            side TEXT NOT NULL CHECK(side IN ('long', 'short')),
            entry_price REAL NOT NULL,
            amount REAL NOT NULL,
            opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (chat_id) REFERENCES users(chat_id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usage_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            analyze_count INTEGER DEFAULT 0,
            news_count INTEGER DEFAULT 0,
            FOREIGN KEY (chat_id) REFERENCES users(chat_id),
            UNIQUE(chat_id, date)
        )
    """)
    conn.commit()