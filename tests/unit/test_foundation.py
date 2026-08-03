"""Smoke tests untuk memastikan semua module foundation bisa di-import."""


def test_import_enums():
    from src.core.types.enums import (
        Side,
        Timeframe,
        Verdict,
    )

    assert Side.LONG == "LONG"
    assert Verdict.SETUP_VALID == "SETUP_VALID"
    assert Timeframe.ONE_HOUR == "1h"


def test_import_exceptions():
    from src.core.exceptions.collector_exceptions import (
        CollectorError,
        DataSourceUnavailableError,
    )
    from src.core.exceptions.signal_exceptions import SignalValidationError

    assert issubclass(DataSourceUnavailableError, CollectorError)
    assert issubclass(SignalValidationError, Exception)


def test_import_models():
    from datetime import datetime, UTC
    from src.core.models.normalized_asset import NormalizedAsset
    from src.core.models.signal_model import SignalResult

    asset = NormalizedAsset(
        symbol="BTC",
        price=50000.0,
        volume_24h=28000000000.0,
        volume_spike_ratio=1.0,
        market_cap=900000000000.0,
        price_change_24h=2.5,
        price_change_7d=-1.2,
        funding_rate=0.0001,
        open_interest=15000000000.0,
        long_short_ratio=1.25,
        fear_greed_value=25,
        fear_greed_classification="Extreme Fear",
        news_headlines=["Test headline"],
        candles_4h=[],
        candles_1h=[],
        data_quality_score=1.0,
        timestamp=datetime.now(UTC),
    )
    assert asset.symbol == "BTC"
    assert asset.price == 50000.0

    signal = SignalResult(
        symbol="BTC",
        pair="BTC/USDT",
        side="LONG",
        entry_price=50000.0,
        target_price=55000.0,
        stop_loss=48000.0,
    )
    assert signal.pair == "BTC/USDT"


def test_import_interfaces():
    from src.core.interfaces.base_analyzer import BaseAnalyzer
    from src.core.interfaces.base_collector import BaseCollector
    from src.core.interfaces.base_engine import BaseEngine

    assert BaseCollector.__abstractmethods__ is not None
    assert BaseAnalyzer.__abstractmethods__ is not None
    assert BaseEngine.__abstractmethods__ is not None


def test_import_settings():
    import os

    os.environ["TELEGRAM_BOT_TOKEN"] = "test"
    os.environ["ADMIN_CHAT_ID"] = "123"
    os.environ["ANTHROPIC_API_KEY"] = "test"
    os.environ["TURSO_DATABASE_URL"] = "test"
    os.environ["TURSO_AUTH_TOKEN"] = "test"

    from config.settings import Settings

    s = Settings()
    assert s.TELEGRAM_BOT_TOKEN == "test"
