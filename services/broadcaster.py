# services/broadcaster.py
import asyncio
from db.database import get_connection
from loguru import logger


def get_premium_users() -> list:
    """Return list chat_id semua user premium/elite/admin."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id FROM users WHERE plan IN ('premium', 'elite', 'admin')")
    rows = cursor.fetchall()
    conn.close()
    return [row["chat_id"] if isinstance(row, dict) else row[0] for row in rows]


async def broadcast_signals(bot, signals: list):
    """Kirim signal ke semua user premium/elite/admin."""
    if not signals:
        logger.info("Tidak ada signal untuk broadcast (list kosong)")
        return

    users = get_premium_users()
    if not users:
        return

    from utils.formatter import format_broadcast_signal

    for signal in signals[:5]:  # Max 5 signal per broadcast
        message = format_broadcast_signal(signal)
        for chat_id in users:
            try:
                await bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")
                await asyncio.sleep(0.05)  # Hindari flood
            except Exception as e:
                logger.warning(f"Broadcast ke {chat_id} gagal: {e}")
                continue