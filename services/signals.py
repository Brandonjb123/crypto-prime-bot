# services/signals.py
from datetime import datetime
from db.database import get_connection
from loguru import logger
from services.coingecko import get_price
from utils.symbols import SYMBOL_TO_COINGECKO_ID, get_coin_id

def get_signal_stats(chat_id: int) -> dict:
    """Hitung statistik performa sinyal user."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, pair, side, entry_price, target_price, stop_loss, status, result_pct, created_at, closed_at "
        "FROM signals WHERE chat_id = ? AND status != 'open' ORDER BY closed_at DESC",
        (chat_id,),
    )
    closed_rows = cursor.fetchall()

    cursor.execute(
        "SELECT COUNT(*) as open_count FROM signals WHERE chat_id = ? AND status = 'open'",
        (chat_id,),
    )
    open_row = cursor.fetchone()
    conn.close()

    total_closed = len(closed_rows) if closed_rows else 0
    hit_target = [r for r in closed_rows if r["status"] == "hit_target"]
    hit_stoploss = [r for r in closed_rows if r["status"] == "hit_stoploss"]

    win_count = len(hit_target)
    loss_count = len(hit_stoploss)
    win_rate = (win_count / total_closed * 100) if total_closed > 0 else 0

    avg_profit = 0.0
    if hit_target:
        avg_profit = sum(r["result_pct"] for r in hit_target) / len(hit_target)

    avg_loss = 0.0
    if hit_stoploss:
        avg_loss = sum(r["result_pct"] for r in hit_stoploss) / len(hit_stoploss)

    open_count = open_row["open_count"] if open_row else 0

    return {
        "total_closed": total_closed,
        "win_count": win_count,
        "loss_count": loss_count,
        "win_rate": win_rate,
        "avg_profit": avg_profit,
        "avg_loss": avg_loss,
        "open_count": open_count,
    }

async def check_and_update_signal(signal: dict) -> dict:
    """Cek apakah sinyal sudah kena target atau stop loss."""
    pair = signal["pair"]
    side = signal["side"]
    entry = signal["entry_price"]
    target = signal["target_price"]
    stop = signal["stop_loss"]

    coin_id = get_coin_id(pair)
    if not coin_id:
        return signal

    try:
        price_data = await get_price(coin_id)
        current_price = price_data.get("current_price")
        if current_price is None:
            return signal
    except Exception:
        return signal

    new_status = None
    result_pct = 0.0

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

def normalize_pair(pair: str) -> str:
    """
    Pastikan format pair selalu SYMBOL/USDT sebelum disimpan
    ke database.
    """
    pair = pair.upper().strip()
    if "/" in pair:
        return pair
    return f"{pair}/USDT"

def save_signal(chat_id: int, pair: str, side: str, entry_price: float,
                target_price: float, stop_loss: float) -> int:
    """Simpan sinyal baru ke tabel signals, return ID sinyal."""
    pair = normalize_pair(pair)
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
        "SELECT id, pair, side, entry_price, target_price, stop_loss, status, created_at "
        "FROM signals WHERE chat_id = ? AND status = 'open' ORDER BY created_at DESC",
        (chat_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return rows if rows else []


def count_open_signals(chat_id: int) -> int:
    """Hitung jumlah open signal milik user."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM signals WHERE chat_id = ? AND status = 'open'",
        (chat_id,),
    )
    row = cursor.fetchone()
    conn.close()
    if row:
        return row[0] if not isinstance(row, dict) else row["COUNT(*)"]
    return 0


def has_open_signal(chat_id: int, pair: str) -> bool:
    """Cek apakah user sudah punya open signal untuk pair ini."""
    pair = normalize_pair(pair)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id FROM signals WHERE chat_id = ? AND pair = ? AND status = 'open'",
        (chat_id, pair),
    )
    row = cursor.fetchone()
    conn.close()
    return row is not None

# ==================== EARLY WARNING ====================

async def check_near_target_signals() -> list:
    """Cek semua open signal yang mendekati TP/SL (radius 2%)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM signals WHERE status = 'open' AND warned = 0")
    rows = cursor.fetchall()
    conn.close()

    near_signals = []
    for sig in rows:
        sig = dict(sig) if not isinstance(sig, dict) else sig
        pair = sig["pair"]
        coin_id = get_coin_id(pair)
        if not coin_id:
            continue

        try:
            price_data = await get_price(coin_id)
            current_price = price_data.get("current_price")
            if not current_price:
                continue
        except Exception:
            continue

        target = sig["target_price"]
        sl = sig["stop_loss"]
        target_distance = abs(current_price - target) / target
        sl_distance = abs(current_price - sl) / sl

        if target_distance <= 0.02:
            near_signals.append({"signal": sig, "current_price": current_price, "type": "near_tp"})
        elif sl_distance <= 0.02:
            near_signals.append({"signal": sig, "current_price": current_price, "type": "near_sl"})

    return near_signals


def mark_signal_warned(signal_id: int):
    """Tandai signal sudah dikirim warning."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE signals SET warned = 1 WHERE id = ?", (signal_id,))
    conn.commit()
    conn.close()


def get_signal_summary() -> dict:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM signals WHERE status = 'open'")
    open_row = cursor.fetchone()
    total_open = open_row[0] if not isinstance(open_row, dict) else open_row["COUNT(*)"]

    cursor.execute("SELECT COUNT(*) FROM signals WHERE status != 'open'")
    closed_row = cursor.fetchone()
    total_closed = closed_row[0] if not isinstance(closed_row, dict) else closed_row["COUNT(*)"]

    cursor.execute("SELECT COUNT(*) FROM signals WHERE status != 'open' AND result_pct > 0")
    win_row = cursor.fetchone()
    win_count = win_row[0] if not isinstance(win_row, dict) else win_row["COUNT(*)"]

    loss_count = total_closed - win_count
    win_rate = round((win_count / total_closed * 100), 1) if total_closed > 0 else 0.0

    conn.close()
    return {
        "total_open": total_open,
        "total_closed": total_closed,
        "win_count": win_count,
        "loss_count": loss_count,
        "win_rate": win_rate,
    }


def get_today_activity() -> dict:
    conn = get_connection()
    cursor = conn.cursor()
    today = datetime.utcnow().strftime("%Y-%m-%d")
    cursor.execute("SELECT SUM(analyze_count), SUM(news_count) FROM usage_log WHERE date = ?", (today,))
    row = cursor.fetchone()
    conn.close()

    analyze_count = 0
    news_count = 0

    if row:
        # Handle Turso dict format
        if isinstance(row, dict):
            raw_analyze = row.get("SUM(analyze_count)")
            raw_news = row.get("SUM(news_count)")
        else:
            raw_analyze = row[0]
            raw_news = row[1]

        # Handle nilai null/None dari database
        if raw_analyze and not isinstance(raw_analyze, dict):
            analyze_count = int(raw_analyze)
        if raw_news and not isinstance(raw_news, dict):
            news_count = int(raw_news)

    return {"analyze_count": analyze_count, "news_count": news_count}    