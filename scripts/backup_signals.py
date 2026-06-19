# scripts/backup_signals.py
import json
from db.database import get_connection

def backup_signals():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM signals")
    rows = cursor.fetchall()
    
    data = []
    for row in rows:
        if isinstance(row, dict):
            data.append(row)
        else:
            data.append(list(row))
    
    with open("signals_backup_pre_reset.json", "w") as f:
        json.dump(data, f, indent=2, default=str)
    
    print(f"Backup selesai: {len(data)} signal disimpan")
    conn.close()

if __name__ == "__main__":
    backup_signals()