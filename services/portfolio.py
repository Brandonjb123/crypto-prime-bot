# services/portfolio.py
from db.database import get_connection


def add_position(chat_id: int, pair: str, side: str, entry_price: float, amount: float) -> int:
    """Tambah posisi baru, return ID posisi."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO positions (chat_id, pair, side, entry_price, amount) "
        "VALUES (?, ?, ?, ?, ?) RETURNING id",
        (chat_id, pair.upper(), side.lower(), entry_price, amount),
    )
    row = cursor.fetchone()
    conn.commit()
    position_id = row["id"] if row else 0
    return position_id


def get_positions(chat_id: int) -> list:
    """Ambil semua posisi user, return list of dict."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, pair, side, entry_price, amount, opened_at FROM positions "
        "WHERE chat_id = ? ORDER BY opened_at DESC",
        (chat_id,),
    )
    rows = cursor.fetchall()
    return rows if rows else []


def remove_position(chat_id: int, position_id: int) -> bool:
    """Hapus posisi berdasarkan ID. Return True jika berhasil."""
    conn = get_connection()
    cursor = conn.cursor()
    # Cek dulu apakah posisi ada
    cursor.execute(
        "SELECT id FROM positions WHERE id = ? AND chat_id = ?",
        (position_id, chat_id),
    )
    if cursor.fetchone():
        cursor.execute(
            "DELETE FROM positions WHERE id = ? AND chat_id = ?",
            (position_id, chat_id),
        )
        conn.commit()
        return True
    return False


def calculate_pnl(entry_price: float, current_price: float, side: str) -> float:
    """Hitung persentase profit/loss."""
    if side == "long":
        return ((current_price - entry_price) / entry_price) * 100
    elif side == "short":
        return ((entry_price - current_price) / entry_price) * 100
    return 0.0