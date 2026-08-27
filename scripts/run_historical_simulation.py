"""Script untuk menjalankan simulasi historis dengan data real dari Binance Vision."""

import asyncio

import httpx

from src.bootstrap.container import Container
from src.simulation.historical_simulation import HistoricalSimulationRunner

SYMBOLS = ["BTC", "ETH", "BNB", "SOL", "XRP", "DOGE", "ADA", "AVAX", "LINK"]
BINANCE_KLINE_URL = "https://data-api.binance.vision/api/v3/klines"


async def fetch_klines(symbol: str, interval: str = "4h", limit: int = 200) -> list[list]:
    params = {
        "symbol": f"{symbol}USDT",
        "interval": interval,
        "limit": limit,
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(BINANCE_KLINE_URL, params=params)
        resp.raise_for_status()
        return resp.json()


async def main():
    container = Container()

    runner = HistoricalSimulationRunner(
        indicator_engine=container.pipeline_runner.indicator_engine,
        analysis_engine=container.pipeline_runner.analysis_engine,
        decision_engine=container.pipeline_runner.decision_engine,
        validation_engine=container.pipeline_runner.validation_engine,
        risk_engine=container.pipeline_runner.risk_engine,
        signal_engine=container.pipeline_runner.signal_engine,
        paper_trading_engine=container.paper_trading_engine,
        lifecycle_engine=container.lifecycle_engine,
        price_provider=container.price_provider,
    )

    for sym in SYMBOLS:
        print(f"Running simulation for {sym}...")
        candles = await fetch_klines(sym)
        result = await runner.run_asset(sym, candles)
        print(
            f"{sym}: closed={len(result.closed_trades)}, wins={result.win_count}, "
            f"losses={result.loss_count}, pnl={result.total_pnl:.2f}"
        )


if __name__ == "__main__":
    asyncio.run(main())