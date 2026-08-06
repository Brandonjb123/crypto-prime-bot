"""Unit tests untuk InMemoryPriceProvider."""

from src.market.in_memory_price_provider import InMemoryPriceProvider


class TestInMemoryPriceProvider:
    def provider(self):
        return InMemoryPriceProvider()

    def test_update_and_get_price(self):
        p = self.provider()
        p.update_price("BTC/USDT", 50000.0)
        assert p.get_price("BTC/USDT") == 50000.0

    def test_overwrite_price(self):
        p = self.provider()
        p.update_price("BTC/USDT", 50000.0)
        p.update_price("BTC/USDT", 51000.0)
        assert p.get_price("BTC/USDT") == 51000.0

    def test_get_unknown_symbol(self):
        p = self.provider()
        assert p.get_price("ETH/USDT") is None

    def test_deterministic(self):
        p1 = InMemoryPriceProvider()
        p2 = InMemoryPriceProvider()
        p1.update_price("BTC/USDT", 50000.0)
        p2.update_price("BTC/USDT", 50000.0)
        assert p1.get_price("BTC/USDT") == p2.get_price("BTC/USDT")