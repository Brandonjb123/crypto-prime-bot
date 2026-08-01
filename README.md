# Crypto Prime Bot v2.0

AI-powered crypto trading assistant — modular, testable, production-ready.

## Branch

- `main` — v1.x stable (production)
- `v2-dev` — v2.0 development (Sprint 0 foundation)

## Quick Start

```bash
git checkout v2-dev
pip install -r requirements.txt
python main.py


Project Structure
text
src/
├── core/           # Types, models, interfaces, exceptions
├── shared/         # Logger, cache, rate limiter
├── collectors/     # Data collectors (Sprint 1+)
├── normalizer/     # Data normalization (Sprint 2+)
├── analysis/       # 9 analysis modules (Sprint 3-5)
├── detection/      # Signal detection (Sprint 6)
├── confidence/     # Confidence engine (Sprint 7)
├── validator/      # Signal validation (Sprint 7)
├── risk/           # Risk management (Sprint 8)
├── analyst/        # LLM reasoning (Sprint 9)
├── recommendation/ # Final recommendation (Sprint 9)
└── delivery/       # Telegram bot (Sprint 10)


Sprint Status
Sprint	Status
0 — Foundation	✅ Done
1 — Collectors	🔜 Next
text

Simpan.

---

**Langkah berikutnya:** install dependensi baru dan test.

Jalankan ini di terminal (pastikan virtualenv aktif):

```cmd
pip install ruff pytest pytest-asyncio pytest-cov pydantic pydantic-settings python-dotenv --upgrade
pip freeze > requirements.txt
Setelah itu, kita bisa test dengan:

cmd
python main.py
pytest tests/ -v