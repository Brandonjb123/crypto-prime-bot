"""Smoke tests untuk memastikan semua module foundation bisa di-import."""


def test_import_enums():
    from src.core.types.enums import (
        Side,
        Verdict,
        Timeframe,
        TrendDirection,
        ConfidenceLevel,
        VolumeSignal,
        MarketStructure,
        SentimentLevel,
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
    from src.core.models.normalized_asset import NormalizedAsset
    from src.core.models.signal_model import SignalResult

    asset = NormalizedAsset(symbol="BTC", current_price=50000.0)
    assert asset.symbol == "BTC"

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
    from src.core.interfaces.base_collector import BaseCollector
    from src.core.interfaces.base_analyzer import BaseAnalyzer
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