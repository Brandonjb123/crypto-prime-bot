# Sprint 0 — Foundation

**Branch:** `v2-dev`  
**Status:** ✅ Complete  
**Goal:** Zero fitur trading, 100% fondasi

---

## Deliverables Checklist

- [x] Branch `v2-dev` dibuat dari `main`
- [x] Struktur folder lengkap
- [x] `__init__.py` di semua package
- [x] `config/settings.py` — configuration management
- [x] `config/constants.py` — project constants
- [x] `.env.example` — template environment variables
- [x] `pyproject.toml` — ruff + pytest + mypy config
- [x] `src/core/types/enums.py` — semua enums
- [x] `src/core/types/asset.py` — Asset model
- [x] `src/core/types/signal.py` — Signal + AnalysisResult models
- [x] `src/core/models/normalized_asset.py` — NormalizedAsset model
- [x] `src/core/models/signal_model.py` — SignalResult + DetectionBatch models
- [x] `src/core/interfaces/base_collector.py` — BaseCollector ABC
- [x] `src/core/interfaces/base_analyzer.py` — BaseAnalyzer ABC
- [x] `src/core/interfaces/base_engine.py` — BaseEngine ABC
- [x] `src/core/exceptions/collector_exceptions.py` — Collector exception hierarchy
- [x] `src/core/exceptions/analysis_exceptions.py` — Analysis exception hierarchy
- [x] `src/core/exceptions/signal_exceptions.py` — Signal exception hierarchy
- [x] `src/shared/logger.py` — Logging framework (loguru)
- [x] `src/shared/cache.py` — Simple in-memory cache
- [x] `src/shared/rate_limiter.py` — Async rate limiter
- [x] `tests/unit/test_foundation.py` — Smoke tests (6 tests)
- [x] `.github/workflows/ci.yml` — CI/CD pipeline
- [x] `docs/TDD_v1.0.md` — TDD documentation
- [x] `docs/sprints/SPRINT_0.md` — Sprint report (file ini)
- [x] `docs/sprints/SPRINT_TEMPLATE.md` — Sprint template
- [x] `main.py` — Entry point minimal
- [x] `requirements.txt` — Updated dependencies
- [x] `README.md` — Updated project documentation

---

## Coding Standards

- Formatter: ruff (line-length 100, double quotes)
- Linter: ruff (E, F, I, UP, B rules)
- Type hints: wajib di semua function
- Docstring: wajib di semua public class
- Import sorting: otomatis oleh ruff

---

## Testing

- Framework: pytest + pytest-asyncio + pytest-cov
- Smoke test: `tests/unit/test_foundation.py` (6 tests)
- Run: `pytest tests/ -v`

---

## Notes

- Tidak ada logic trading, API calls, atau database operations di Sprint 0
- Semua module hanya berisi interface, types, exceptions, dan foundation utilities
- Project siap untuk Sprint 1 — Data Collectors