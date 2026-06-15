# db/models.py
from db.database import get_connection


def register_user(chat_id: int, username: str = None, first_name: str = None):
    """Daftarkan user baru jika belum ada. Return True jika user baru, False jika sudah ada."""
    conn = get_connection()
    cursor = conn.cursor()

    # Cek apakah user sudah ada
    cursor.execute("SELECT chat_id FROM users WHERE chat_id = ?", (chat_id,))
    if cursor.fetchone():
        conn.close()
        return False  # user sudah terdaftar

    # Insert user baru
    cursor.execute(
        "INSERT INTO users (chat_id, username, first_name) VALUES (?, ?, ?)",
        (chat_id, username, first_name),
    )
    conn.commit()
    conn.close()
    return True


def get_user(chat_id: int):
    """Ambil data user berdasarkan chat_id."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE chat_id = ?", (chat_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None