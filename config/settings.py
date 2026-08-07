from pydantic_settings import BaseSettings
from dotenv import load_dotenv
load_dotenv()

class Settings(BaseSettings):
    # Telegram
    TELEGRAM_BOT_TOKEN: str
    ADMIN_CHAT_ID: int

    # LLM
    OPENROUTER_API_KEY: str

    # Database
    TURSO_DATABASE_URL: str
    TURSO_AUTH_TOKEN: str

    # Logging
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "production"

    # Trading Parameters
    PRIMARY_TIMEFRAME: str = "4h"
    CONFIRMATION_TIMEFRAME: str = "1h"
    CONFIDENCE_THRESHOLD_HIGH: float = 0.75
    CONFIDENCE_THRESHOLD_MEDIUM: float = 0.60
    MIN_VOLUME_USD: float = 5_000_000
    MIN_DATA_QUALITY_SCORE: float = 0.70
    SIGNAL_EXPIRY_HOURS: int = 4
    ATR_MULTIPLIER_TP1: float = 1.0
    ATR_MULTIPLIER_TP2: float = 2.0
    ATR_MULTIPLIER_TP3: float = 3.0
    ATR_MULTIPLIER_SL: float = 0.75

    model_config = {"env_file": ".env", "case_sensitive": True}


settings = Settings()
