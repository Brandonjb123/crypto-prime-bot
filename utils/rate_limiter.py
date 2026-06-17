# utils/rate_limiter.py
from datetime import datetime
from db.database import get_connection

PLAN_LIMITS = {
    "free": {"analyze": 3, "news": 5},
    "premium": {"analyze": 30, "news": 50},
    "elite": {"analyze": 999999, "news": 999999},
    "admin": {"analyze": 999999, "news": 999999},
}


def get_limit(plan: str, command: str) -> int:
    """Return limit harian berdasarkan plan dan command."""
    return PLAN_LIMITS.get(plan, PLAN_LIMITS["free"]).get(command, 0)


def check_and_increment(chat_id: int, command: str, plan: str = "free") -> bool:
    """
    Return True kalau masih dalam limit (dan increment count).
    Return False kalau sudah habis.
    Untuk admin, selalu return True tanpa increment.
    """
    if plan == "admin":
        return True

    limit = get_limit(plan, command)
    if limit == 0:
        return False

    conn = get_connection()
    cursor = conn.cursor()
    today = datetime.utcnow().strftime("%Y-%m-%d")

    # Cek count hari ini
    cursor.execute(
        f"SELECT {command}_count FROM usage_log WHERE chat_id = ? AND date = ?",
        (chat_id, today),
    )
    row = cursor.fetchone()

    if row:
        current = row[f"{command}_count"] if isinstance(row, dict) else row[0]
        current = int(current) if current else 0
    else:
        current = 0

    if current >= limit:
        conn.close()
        return False

    # Increment
    if row:
        cursor.execute(
            f"UPDATE usage_log SET {command}_count = {command}_count + 1 WHERE chat_id = ? AND date = ?",
            (chat_id, today),
        )
    else:
        # Buat baris baru dengan count = 1 untuk command ini, 0 untuk lainnya
        other = "news" if command == "analyze" else "analyze"
        cursor.execute(
            f"INSERT INTO usage_log (chat_id, date, {command}_count, {other}_count) VALUES (?, ?, 1, 0)",
            (chat_id, today),
        )

    conn.commit()
    conn.close()
    return True


def get_remaining(chat_id: int, plan: str = "free") -> dict:
    """Return sisa kuota hari ini dalam dict."""
    conn = get_connection()
    cursor = conn.cursor()
    today = datetime.utcnow().strftime("%Y-%m-%d")

    cursor.execute(
        "SELECT analyze_count, news_count FROM usage_log WHERE chat_id = ? AND date = ?",
        (chat_id, today),
    )
    row = cursor.fetchone()
    conn.close()

    if row:
        used_analyze = int(row["analyze_count"]) if isinstance(row, dict) else int(row[0])
        used_news = int(row["news_count"]) if isinstance(row, dict) else int(row[1])
    else:
        used_analyze = 0
        used_news = 0

    analyze_limit = get_limit(plan, "analyze")
    news_limit = get_limit(plan, "news")

    return {
        "analyze_remaining": max(0, analyze_limit - used_analyze),
        "news_remaining": max(0, news_limit - used_news),
        "plan": plan,
    }