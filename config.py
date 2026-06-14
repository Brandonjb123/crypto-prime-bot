# config.py
import os
import sys
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
CCDATA_API_KEY = os.getenv("CCDATA_API_KEY", "placeholder")

# Debug: print keberadaan token (tanpa menampilkan token lengkap)
if TELEGRAM_BOT_TOKEN:
    print(f"✅ TELEGRAM_BOT_TOKEN ditemukan: ...{TELEGRAM_BOT_TOKEN[-10:]}")
else:
    print("❌ TELEGRAM_BOT_TOKEN TIDAK DITEMUKAN di environment")

if GROQ_API_KEY:
    print(f"✅ GROQ_API_KEY ditemukan: ...{GROQ_API_KEY[-10:]}")
else:
    print("❌ GROQ_API_KEY TIDAK DITEMUKAN di environment")

# Jangan crash jika token tidak ada, biarkan bot jalan dan error nanti saat dipakai