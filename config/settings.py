from dotenv import load_dotenv
from pydantic import model_validator
from pydantic_settings import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    # Telegram
    TELEGRAM_BOT_TOKEN: str
    ADMIN_CHAT_ID: int

    # Exchange Testnet
    EXCHANGE_API_KEY: str = ""
    EXCHANGE_API_SECRET: str = ""
    EXCHANGE_ENV: str = "TESTNET"

    # Trading Mode
    TRADING_MODE: str = "PAPER"
    LIVE_TRADING_ENABLED: bool = False

    # LLM
    LLM_PROVIDER: str = "openrouter"  # openrouter | groq
    OPENROUTER_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

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

    @model_validator(mode="after")
    def _validate_runtime_config(self):
        # LIVE trading validation
        if self.TRADING_MODE.upper() == "LIVE":
            if not self.LIVE_TRADING_ENABLED:
                raise ValueError("TRADING_MODE=LIVE requires LIVE_TRADING_ENABLED=true")
            if self.EXCHANGE_ENV.upper() != "TESTNET":
                raise ValueError("Sprint 12B only supports EXCHANGE_ENV=TESTNET")
            if not self.EXCHANGE_API_KEY or not self.EXCHANGE_API_SECRET:
                raise ValueError("EXCHANGE_API_KEY and EXCHANGE_API_SECRET are required for LIVE mode")

        # LLM provider validation
        provider = self.LLM_PROVIDER.lower()
        if provider not in ("openrouter", "groq"):
            raise ValueError(f"Invalid LLM_PROVIDER: {self.LLM_PROVIDER}. Must be 'openrouter' or 'groq'")
        if provider == "openrouter" and not self.OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY is required when LLM_PROVIDER=openrouter")
        if provider == "groq" and not self.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is required when LLM_PROVIDER=groq")

        return self


settings = Settings()