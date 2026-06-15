# db/database.py
import os
import sqlite3
from turso_python import TursoConnection
from loguru import logger

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
        remaining = self._rows[self._index:]
        self._index = len(self._rows)
        return remaining

    def execute(self, sql, params=None):
        # Ganti placeholder ? dengan nilai parameter
        if params:
            for param in params:
                if isinstance(param, str):
                    sql = sql.replace("?", f"'{param}'", 1)
                else:
                    sql = sql.replace("?", str(param), 1)

        # Eksekusi query via Turso
        raw_result = self._conn._conn.execute_query(sql)

        # Parsing hasil dari struktur respons Turso
        rows = []
        if isinstance(raw_result, dict) and "results" in raw_result:
            for item in raw_result["results"]:
                if item.get("type") == "ok":
                    response = item.get("response", {})
                    result = response.get("result", {})
                    # Ambil kolom untuk pemetaan nama
                    cols = [col["name"] for col in result.get("cols", [])]
                    # Ambil baris data
                    raw_rows = result.get("rows", [])
                    for row in raw_rows:
                        converted_row = []
                        for cell in row:
                            val = cell.get("value", cell)
                            # Konversi tipe data sesuai type dari Turso
                            if cell.get("type") == "integer":
                                val = int(val)
                            elif cell.get("type") == "real":
                                val = float(val)
                            # text dan lainnya biarkan apa adanya
                            converted_row.append(val)

                        # Jika ada kolom, buat dictionary; jika tidak, simpan sebagai list
                        if cols:
                            row_dict = {}
                            for i, col_name in enumerate(cols):
                                row_dict[col_name] = converted_row[i] if i < len(converted_row) else None
                            rows.append(row_dict)
                        else:
                            rows.append(converted_row)

        self._rows = rows
        self.rowcount = len(rows)
        self._index = 0
        self.description = None
        logger.info(f"QUERY: {sql} → ROWS PARSED: {self._rows}")
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
        pass

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