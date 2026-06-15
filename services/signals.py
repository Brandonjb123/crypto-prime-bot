# services/signals.py
from datetime import datetime
from db.database import get_connection
from loguru import logger


def save_signal(chat_id: int, pair: str, side: str, entry_price: float,
                target_price: float, stop_loss: float) -> int:
    """Simpan sinyal baru ke tabel signals, return ID sinyal."""
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()

    cursor.execute(
        "INSERT INTO signals (chat_id, pair, side, entry_price, target_price, "
        "stop_loss, status, created_at) VALUES (?, ?, ?, ?, ?, ?, 'open', ?) "
        "RETURNING id",
        (chat_id, pair.upper(), side.lower(), entry_price, target_price, stop_loss, now)
    )
    conn.commit()
    row = cursor.fetchone()

    if row:
        signal_id = row["id"] if isinstance(row, dict) else row[0]
        logger.info(f"Sinyal #{signal_id} disimpan: {pair} {side}")
        return signal_id
    return 0


def get_open_signals(chat_id: int) -> list:
    """Ambil semua sinyal open milik user."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, pair, side, entry_price, target_price, stop_loss, created_at "
        "FROM signals WHERE chat_id = ? AND status = 'open' ORDER BY created_at DESC",
        (chat_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return rows if rows else []
