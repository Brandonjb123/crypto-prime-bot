# db/database.py
import sqlite3
import os
from pathlib import Path

DB_PATH = os.getenv("DB_PATH", str(Path(__file__).parent.parent / "crypto_prime.db"))

def get_connection():
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