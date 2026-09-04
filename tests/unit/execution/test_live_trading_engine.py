import asyncio
from unittest.mock import MagicMock
from uuid import uuid4

from src.core.types.enums import OrderStatus
from src.execution.exchange.mock_client import MockExchangeClient
from src.execution.live_trading_engine import LiveTradingEngine


def make_signal():
    signal = MagicMock()
    signal.signal_id = uuid4()
    signal.symbol = "BTCUSDT"
    signal.side = "LONG"
    signal.position_size = 0.01
    signal.entry_price = 50000.0
    signal.stop_loss = 49000.0
    signal.take_profit = 52000.0
    return signal


class TestLiveTradingEngine:
    def test_fill_immediately(self):
        exchange = MockExchangeClient(behavior="fill_immediately")
        engine = LiveTradingEngine(exchange)
        result = asyncio.run(engine.execute(make_signal()))

        assert result.status == OrderStatus.FILLED
        assert result.position_size == 0.01

    def test_reject(self):
        exchange = MockExchangeClient(behavior="reject")
        engine = LiveTradingEngine(exchange)
        result = asyncio.run(engine.execute(make_signal()))

        assert result.status == OrderStatus.REJECTED

    def test_partial_fill(self):
        exchange = MockExchangeClient(behavior="partial_fill")
        engine = LiveTradingEngine(exchange)
        result = asyncio.run(engine.execute(make_signal()))

        assert result.status == OrderStatus.PARTIALLY_FILLED

    def test_timeout(self):
        exchange = MockExchangeClient(behavior="timeout")
        engine = LiveTradingEngine(exchange)
        result = asyncio.run(engine.execute(make_signal()))

        assert result.status == OrderStatus.UNKNOWN

    def test_network_error(self):
        exchange = MockExchangeClient(behavior="network_error")
        engine = LiveTradingEngine(exchange)
        result = asyncio.run(engine.execute(make_signal()))

        assert result.status == OrderStatus.FAILED

    def test_idempotency(self):
        exchange = MockExchangeClient(behavior="fill_immediately")
        engine = LiveTradingEngine(exchange)
        signal = make_signal()  # signal_id tetap sama

        # Panggil pertama — eksekusi normal
        result1 = asyncio.run(engine.execute(signal))

        # Panggil kedua dengan signal SAMA — harus kena idempotensi
        result2 = asyncio.run(engine.execute(signal))

        # Order kedua harus return order yang sama (idempotent)
        assert result1.execution_id == result2.execution_id