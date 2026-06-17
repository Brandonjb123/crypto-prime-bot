# db/models.py
from datetime import datetime, timedelta
from db.database import get_connection
from loguru import logger


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
    """Return plan user saat ini. Otomatis downgrade ke free kalau expired."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT plan, plan_expiry FROM users WHERE chat_id = ?", (chat_id,))
    row = cursor.fetchone()
    
    if row is None:
        conn.close()
        return "free"
    
    plan = row["plan"] if isinstance(row, dict) else (row[0] or "free")
    expiry_str = row["plan_expiry"] if isinstance(row, dict) else row[1]

    if expiry_str and plan not in ("free", "admin"):
        try:
            expiry = datetime.fromisoformat(expiry_str)
            if datetime.utcnow() > expiry:
                # Expired → downgrade ke free
                cursor.execute(
                    "UPDATE users SET plan = 'free', plan_expiry = NULL WHERE chat_id = ?",
                    (chat_id,),
                )
                conn.commit()
                conn.close()
                return "free"
        except Exception:
            pass

    conn.close()
    return plan or "free"


def set_user_plan(chat_id: int, plan: str, days: int = None) -> bool:
    """Set plan user. days=30 untuk 30 hari, None untuk permanen."""
    if plan not in ("free", "premium", "elite", "admin"):
        return False

    conn = get_connection()
    cursor = conn.cursor()

    if days and plan not in ("free", "admin"):
        expiry = (datetime.utcnow() + timedelta(days=days)).isoformat()
        cursor.execute(
            "UPDATE users SET plan = ?, plan_expiry = ? WHERE chat_id = ?",
            (plan, expiry, chat_id),
        )
    else:
        cursor.execute(
            "UPDATE users SET plan = ?, plan_expiry = NULL WHERE chat_id = ?",
            (plan, chat_id),
        )

    conn.commit()
    conn.close()
    return True