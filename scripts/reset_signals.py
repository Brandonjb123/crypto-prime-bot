# scripts/reset_signals.py
from db.database import get_connection

def reset_signals():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM signals")
    conn.commit()
    print("Semua data signals sudah direset ke 0")
    conn.close()

if __name__ == "__main__":
    reset_signals()