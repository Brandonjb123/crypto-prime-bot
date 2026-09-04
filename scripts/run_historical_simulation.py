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


async def fetch_klines(symbol: str, interval: str = "4h", limit: int = 1000) -> list[list]:
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

        # Chronological out-of-sample split: 70% dev / 30% oos
        split_idx = int(len(candles) * 0.7)
        dev_candles = candles[:split_idx]
        oos_candles = candles[split_idx:]

        print(f"  DEV period ({len(dev_candles)} candles)...")
        dev_result = await runner.run_asset(sym, dev_candles)

        print(f"  OOS period ({len(oos_candles)} candles)...")
        oos_result = await runner.run_asset(sym, oos_candles)

        print(
            f"{sym}: DEV closed={len(dev_result.closed_trades)}, wins={dev_result.win_count}, losses={dev_result.loss_count}, pnl={dev_result.total_pnl:.2f}, "
            f"valid_dec={dev_result.valid_decision_count}, ai_unav={dev_result.ai_unavailable_count}, buys={dev_result.buy_signals}, sells={dev_result.sell_signals}, waits={dev_result.wait_signals}"
        )
        print(
            f"{sym}: OOS closed={len(oos_result.closed_trades)}, wins={oos_result.win_count}, losses={oos_result.loss_count}, pnl={oos_result.total_pnl:.2f}, "
            f"valid_dec={oos_result.valid_decision_count}, ai_unav={oos_result.ai_unavailable_count}, buys={oos_result.buy_signals}, sells={oos_result.sell_signals}, waits={oos_result.wait_signals}"
        )


if __name__ == "__main__":
    asyncio.run(main())