# services/broadcaster.py
import asyncio
from db.database import get_connection
from loguru import logger
from services.signals import save_signal, has_open_signal, count_open_signals
from db.models import get_user_plan
from utils.rate_limiter import MAX_OPEN_SIGNALS


def get_premium_users() -> list:
    """Return list chat_id semua user premium/elite/admin."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id FROM users WHERE plan IN ('premium', 'elite', 'admin')")
    rows = cursor.fetchall()
    conn.close()
    return [row["chat_id"] if isinstance(row, dict) else row[0] for row in rows]


async def broadcast_signals(bot, signals: list):
    """
    Kirim signal ke semua user premium/elite, DAN simpan signal
    ke database untuk masing-masing user (supaya tercatat di
    /mysignals dan ikut dihitung di /paperstats).
    """
    if not signals:
        logger.info("Tidak ada signal untuk broadcast (list kosong)")
        return

    users = get_premium_users()
    if not users:
        return

    from utils.formatter import format_broadcast_signal

    for signal in signals[:5]:  # Max 5 signal per broadcast
        pair = signal.get("pair", "Unknown")
        side = signal.get("side", "LONG")
        entry_price = signal.get("entry_price", 0)
        target_price = signal.get("target_price", 0)
        stop_loss = signal.get("stop_loss", 0)
        message = format_broadcast_signal(signal)

        for chat_id in users:
            try:
                # Cek dedup & limit (sama seperti logic run_analyze)
                plan = get_user_plan(chat_id)
                max_signals = MAX_OPEN_SIGNALS.get(plan, 5)
                current_count = count_open_signals(chat_id)

                should_save = (
                    not has_open_signal(chat_id, pair) and
                    current_count < max_signals
                )

                if should_save:
                    # Simpan signal untuk user ini
                    save_signal(
                        chat_id=chat_id,
                        pair=pair,
                        side=side.lower(),
                        entry_price=float(entry_price),
                        target_price=float(target_price),
                        stop_loss=float(stop_loss),
                    )

                # Kirim pesan tetap dilakukan untuk SEMUA user
                await bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode="Markdown"
                )
                await asyncio.sleep(0.05)  # Hindari flood
            except Exception as e:
                logger.warning(f"Broadcast ke {chat_id} gagal: {e}")
                continue