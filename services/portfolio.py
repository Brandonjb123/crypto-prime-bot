# services/portfolio.py
from db.database import get_connection


def add_position(chat_id: int, pair: str, side: str, entry_price: float, amount: float) -> int:
    """Tambah posisi baru, return ID posisi."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO positions (chat_id, pair, side, entry_price, amount) VALUES (?, ?, ?, ?, ?)",
        (chat_id, pair.upper(), side.lower(), entry_price, amount),
    )
    conn.commit()
    position_id = cursor.lastrowid
    conn.close()
    return position_id


def get_positions(chat_id: int) -> list:
    """Ambil semua posisi user, return list of dict."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, pair, side, entry_price, amount, opened_at FROM positions WHERE chat_id = ? ORDER BY opened_at DESC",
        (chat_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def remove_position(chat_id: int, position_id: int) -> bool:
    """Hapus posisi berdasarkan ID. Return True jika berhasil."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM positions WHERE id = ? AND chat_id = ?",
        (position_id, chat_id),
    )
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted


def calculate_pnl(entry_price: float, current_price: float, side: str) -> float:
    """
    Hitung persentase profit/loss.
    side: 'long' atau 'short'
    Return: persentase P&L (positif = untung, negatif = rugi)
    """
    if side == "long":
        return ((current_price - entry_price) / entry_price) * 100
    elif side == "short":
        return ((entry_price - current_price) / entry_price) * 100
    return 0.0