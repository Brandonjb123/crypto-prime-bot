# Trading pairs default
DEFAULT_TOP_PAIRS_LIMIT = 100

# Rate limiting (detik)
COINGECKO_RATE_LIMIT = 1.2
LLM_RATE_LIMIT = 3.0
NEWS_RATE_LIMIT = 2.0

# Cache TTL (detik)
CACHE_TTL_PRICE = 30
CACHE_TTL_MARKET_DATA = 60
CACHE_TTL_NEWS = 120

# Scanner
SCAN_BATCH_SIZE = 10
SCAN_BATCH_DELAY = 2.0

# Maximum concurrent tasks
MAX_CONCURRENT_API_CALLS = 5


# API Base URLs
BINANCE_FUTURES_URL = "https://fapi.binance.com"
COINGECKO_API_URL = "https://api.coingecko.com/api/v3"
FEAR_GREED_API_URL = "https://api.alternative.me"
GOOGLE_NEWS_RSS_URL = "https://news.google.com/rss/search"

# API Timeouts & Limits
BINANCE_TIMEOUT = 10.0
COINGECKO_TIMEOUT = 15.0
FEAR_GREED_TIMEOUT = 10.0
NEWS_TIMEOUT = 10.0
MAX_NEWS_ARTICLES = 5
MIN_CANDLES_REQUIRED = 20

# Confidence Engine Weights (Sprint 4B)
CONFIDENCE_WEIGHTS = {
    "base_score": 0.5,
    "trend_structure_aligned": 0.15,
    "volume_spike": 0.10,
    "funding_neutral": 0.08,
    "sentiment_aligned": 0.08,
    "price_position_favorable": 0.07,
    "volatility_medium": 0.05,
    "trend_structure_conflict": -0.20,
    "volume_weak": -0.15,
    "sentiment_conflict": -0.10,
    "funding_extreme": -0.08,
    "volatility_high": -0.05,
}

# Setup Detection — Rule Priority Order
RULE_PRIORITY_ORDER = ["reversal", "breakout", "trend_following"]

VALIDATOR_CONFIDENCE_THRESHOLD = 0.60

# Risk Engine Defaults
RISK_PER_TRADE = 0.02       # 2% modal per trade
MAX_POSITION_SIZE = 100.0   # Maksimum 100 unit (contoh: kontrak)
MIN_RISK_REWARD_RATIO = 2.0 # Minimum 1:2

# Risk Engine — ATR Multipliers per Risk Model
ATR_MULTIPLIERS = {
    "trend": {"sl": 2.0, "tp": 4.0},
    "breakout": {"sl": 1.5, "tp": 5.0},
    "reversal": {"sl": 2.5, "tp": 3.5},
}

# Recommendation Engine
READY_EXECUTION_MIN_CONFIDENCE = 0.60
READY_EXECUTION_MIN_RR = 2.0

MAX_PORTFOLIO_EXPOSURE = 300

TELEGRAM_ALLOWED_USERS = []  # Kosong = semua user diizinkan

LOG_LEVEL = "INFO"
MAX_PIPELINE_FAILURES = 5
HEALTH_CHECK_INTERVAL = 60