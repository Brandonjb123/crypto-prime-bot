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