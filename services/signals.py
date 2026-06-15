# services/signals.py
from datetime import datetime
from db.database import get_connection
from loguru import logger
from services.coingecko import get_price
from utils.symbols import SYMBOL_TO_COINGECKO_ID


async def check_and_update_signal(signal: dict) -> dict:
    """
    Cek apakah sinyal sudah kena target atau stop loss berdasarkan harga terkini.
    Return dict dengan status terbaru.
    """
    pair = signal["pair"]
    side = signal["side"]
    entry = signal["entry_price"]
    target = signal["target_price"]
    stop = signal["stop_loss"]

    # Ambil harga terkini
    coin_id = SYMBOL_TO_COINGECKO_ID.get(pair)
    if not coin_id:
        return signal  # tidak bisa cek, kembalikan apa adanya

    try:
        price_data = await get_price(coin_id)
        current_price = price_data.get("current_price")
        if current_price is None:
            return signal
    except Exception:
        return signal

    # Cek status
    new_status = None
    if side == "long":
        if current_price >= target:
            new_status = "hit_target"
            result_pct = ((target - entry) / entry) * 100
        elif current_price <= stop:
            new_status = "hit_stoploss"
            result_pct = ((stop - entry) / entry) * 100
    elif side == "short":
        if current_price <= target:
            new_status = "hit_target"
            result_pct = ((entry - target) / entry) * 100
        elif current_price >= stop:
            new_status = "hit_stoploss"
            result_pct = ((entry - stop) / entry) * 100

    if new_status:
        # Update database
        now = datetime.utcnow().isoformat()
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE signals SET status = ?, result_pct = ?, closed_at = ? WHERE id = ?",
            (new_status, result_pct, now, signal["id"]),
        )
        conn.commit()
        conn.close()

        logger.info(f"Sinyal #{signal['id']} berubah status: {new_status} ({result_pct:+.2f}%)")
        signal["status"] = new_status
        signal["result_pct"] = result_pct
        signal["closed_at"] = now

    return signal


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
