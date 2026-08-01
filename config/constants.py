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