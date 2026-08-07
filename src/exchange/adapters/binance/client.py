"""Binance HTTP client wrapper — mockable, no business logic."""


class BinanceClient:
    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet

    async def place_order(
        self, symbol: str, side: str, quantity: float, price: float | None = None
    ) -> dict:
        """Place order via Binance Futures API. Mockable."""
        raise NotImplementedError("Real HTTP call not implemented yet.")

    async def get_account(self) -> dict:
        """Get account info."""
        raise NotImplementedError("Real HTTP call not implemented yet.")

    async def get_position(self, symbol: str) -> dict | None:
        """Get open position for symbol."""
        raise NotImplementedError("Real HTTP call not implemented yet.")

    async def get_price(self, symbol: str) -> float | None:
        """Get mark price."""
        raise NotImplementedError("Real HTTP call not implemented yet.")
