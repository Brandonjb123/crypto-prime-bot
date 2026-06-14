import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
CCDATA_API_KEY = os.getenv("CCDATA_API_KEY")

assert TELEGRAM_BOT_TOKEN, "TELEGRAM_BOT_TOKEN tidak ada di .env"
assert GROQ_API_KEY, "GROQ_API_KEY tidak ada di .env"
# CCData tidak wajib dulu, jadi tidak di-assert