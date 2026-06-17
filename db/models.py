# db/models.py
from db.database import get_connection


def register_user(chat_id: int, username: str = None, first_name: str = None):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT chat_id FROM users WHERE chat_id = ?", (chat_id,))
    if cursor.fetchone():
        conn.close()
        return False

    cursor.execute(
        "INSERT INTO users (chat_id, username, first_name) VALUES (?, ?, ?)",
        (chat_id, username, first_name),
    )
    conn.commit()
    conn.close()
    return True


def get_user(chat_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE chat_id = ?", (chat_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def get_user_plan(chat_id: int) -> str:
    """Return plan user: 'free', 'premium', atau 'admin'"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT plan FROM users WHERE chat_id = ?", (chat_id,))
    row = cursor.fetchone()
    conn.close()
    if row is None:
        return "free"
    # Jika row adalah dict (Turso), ambil dengan key, jika tuple, ambil index
    if isinstance(row, dict):
        return row.get("plan", "free") or "free"
    return row[0] if row[0] else "free"


def set_user_plan(chat_id: int, plan: str) -> bool:
    """Set plan user. Return True kalau berhasil."""
    if plan not in ("free", "premium", "elite", "admin"):
        return False
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET plan = ? WHERE chat_id = ?", (plan, chat_id))
    conn.commit()
    conn.close()
    return True