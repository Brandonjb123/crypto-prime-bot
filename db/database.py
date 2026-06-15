# db/database.py
import os
import psycopg2
import psycopg2.extras
from loguru import logger

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # Fallback ke SQLite lokal (untuk development laptop)
    import sqlite3
    DB_PATH = os.getenv("DB_PATH", "crypto_prime.db")
    def get_connection():
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
else:
    def get_connection():
        conn = psycopg2.connect(DATABASE_URL)
        conn.cursor_factory = psycopg2.extras.DictCursor
        return conn


def init_db():
    """Buat tabel-tabel yang dibutuhkan jika belum ada."""
    conn = get_connection()
    cursor = conn.cursor()

    if DATABASE_URL:
        # PostgreSQL syntax
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                chat_id BIGINT PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                plan TEXT DEFAULT 'free'
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS positions (
                id SERIAL PRIMARY KEY,
                chat_id BIGINT NOT NULL REFERENCES users(chat_id),
                pair TEXT NOT NULL,
                side TEXT NOT NULL CHECK(side IN ('long', 'short')),
                entry_price REAL NOT NULL,
                amount REAL NOT NULL,
                opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usage_log (
                id SERIAL PRIMARY KEY,
                chat_id BIGINT NOT NULL REFERENCES users(chat_id),
                date TEXT NOT NULL,
                analyze_count INTEGER DEFAULT 0,
                news_count INTEGER DEFAULT 0,
                UNIQUE(chat_id, date)
            )
        """)
    else:
        # SQLite syntax (fallback)
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
    logger.info("Database initialized successfully")