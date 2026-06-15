# db/database.py
import os
import sqlite3
from pathlib import Path

# Cek apakah ada env DB_PATH, kalau tidak pakai path default di /data (untuk Railway)
# atau di root project (untuk local dev)
DB_PATH = os.getenv("DB_PATH", "/data/crypto_prime.db")

# Untuk local dev: fallback ke root project kalau /data tidak bisa ditulis
if not os.path.exists(os.path.dirname(DB_PATH)):
    DB_PATH = str(Path(__file__).parent.parent / "crypto_prime.db")

def get_connection():
    # Pastikan folder tujuan ada
    db_dir = os.path.dirname(DB_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

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
    conn.close()