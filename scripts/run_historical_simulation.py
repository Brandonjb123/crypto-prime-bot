"""Script untuk menjalankan simulasi historis dengan data real dari Binance Vision."""

import asyncio
import sys
from pathlib import Path

import httpx

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.bootstrap.container import Container  # noqa: E402
from src.simulation.historical_simulation import HistoricalSimulationRunner  # noqa: E402

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
        initial_balance=10000.0,
    )

    for sym in SYMBOLS:
        print(f"Running simulation for {sym}...")
        candles = await fetch_klines(sym)
        result = await runner.run_asset(sym, candles)

        print(
            f"{sym}: closed={len(result.closed_trades)}, "
            f"wins={result.win_count}, losses={result.loss_count}, "
            f"pnl={result.total_pnl:.2f}, "
            f"valid_decisions={result.valid_decision_count}, "
            f"ai_unavailable={result.ai_unavailable_count}, "
            f"buys={result.buy_signals}, sells={result.sell_signals}, waits={result.wait_signals}"
        )


if __name__ == "__main__":
    asyncio.run(main())