# TDD v1.0 — Crypto Prime Bot v2.0

## Architecture Overview
Data Collectors → Normalizer → Analysis Modules (9) → Detection → Confidence → Validator → Risk → Recommendation → Analyst (LLM) → Delivery (Telegram)


## 10 Modules

1. **Collectors** — Fetch raw data dari CoinGecko, NewsAPI, dll
2. **Normalizer** — Normalisasi data ke format internal
3. **Analysis** — 9 sub-module: Trend, Market Structure, Volume, Futures, Volatility, Support/Resistance, Sentiment, (2 reserved)
4. **Detection** — Gabungkan hasil analisis → deteksi setup
5. **Confidence** — Weighted scoring engine
6. **Validator** — Validasi sinyal (R:R, entry realism, volume minimum)
7. **Risk** — Posisi sizing, exposure check
8. **Analyst** — LLM multi-factor reasoning
9. **Recommendation** — Final signal packaging
10. **Delivery** — Telegram bot formatter & delivery

## Data Flow
Raw Market Data → NormalizedAsset → AnalysisResult[] → DetectionBatch → ConfidenceScore → ValidatedSignal → RiskAssessment → FinalRecommendation → FormattedMessage → Telegram


## Key Principles

- **Normalized Asset** sebagai single source of truth
- Setiap analysis module independent & testable
- Confidence scoring berbobot (setiap module punya weight)
- Validator mem-filter sinyal tidak layak
- Risk module menghitung position size sebelum delivery
- LLM hanya digunakan di layer Analyst (tidak di analysis modules)