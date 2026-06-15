# utils/rate_limiter.py
from datetime import date
from db.database import get_connection

# Batas harian per user
LIMITS = {
    "analyze": 10,
    "news": 15,
}


def check_and_increment(chat_id: int, action_type: str) -> bool:
    """
    Cek apakah user masih punya kuota untuk action_type hari ini.
    Kalau masih, increment counter dan return True.
    Kalau habis, return False.
    """
    if action_type not in LIMITS:
        return True  # action tidak dibatasi

    today = date.today().isoformat()
    conn = get_connection()
    cursor = conn.cursor()

    # Cek apakah sudah ada log untuk user + tanggal ini
    cursor.execute(
        "SELECT analyze_count, news_count FROM usage_log WHERE chat_id = ? AND date = ?",
        (chat_id, today),
    )
    row = cursor.fetchone()

    if row:
        analyze_count = row["analyze_count"]
        news_count = row["news_count"]
    else:
        # Belum ada log, buat baru
        cursor.execute(
            "INSERT INTO usage_log (chat_id, date, analyze_count, news_count) VALUES (?, ?, 0, 0)",
            (chat_id, today),
        )
        analyze_count = 0
        news_count = 0

    # Cek limit
    if action_type == "analyze" and analyze_count >= LIMITS["analyze"]:
        conn.close()
        return False
    if action_type == "news" and news_count >= LIMITS["news"]:
        conn.close()
        return False

    # Increment counter
    if action_type == "analyze":
        cursor.execute(
            "UPDATE usage_log SET analyze_count = analyze_count + 1 WHERE chat_id = ? AND date = ?",
            (chat_id, today),
        )
    elif action_type == "news":
        cursor.execute(
            "UPDATE usage_log SET news_count = news_count + 1 WHERE chat_id = ? AND date = ?",
            (chat_id, today),
        )

    conn.commit()
    conn.close()
    return True


def get_remaining(chat_id: int) -> dict:
    """Return sisa kuota user hari ini."""
    today = date.today().isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT analyze_count, news_count FROM usage_log WHERE chat_id = ? AND date = ?",
        (chat_id, today),
    )
    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "analyze_remaining": LIMITS["analyze"] - row["analyze_count"],
            "news_remaining": LIMITS["news"] - row["news_count"],
        }
    return {
        "analyze_remaining": LIMITS["analyze"],
        "news_remaining": LIMITS["news"],
    }