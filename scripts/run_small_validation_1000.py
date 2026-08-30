"""Small validation dengan 1000 candle dan OOS split."""

import asyncio
import sys
from pathlib import Path

import httpx

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.bootstrap.container import Container  # noqa: E402
from src.simulation.historical_simulation import HistoricalSimulationRunner  # noqa: E402

SYMBOLS = ["BTC", "ETH", "SOL"]
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
        candles = await fetch_klines(sym)
        split_idx = int(len(candles) * 0.7)
        dev_candles = candles[:split_idx]
        oos_candles = candles[split_idx:]

        dev_result = await runner.run_asset(sym, dev_candles)
        oos_result = await runner.run_asset(sym, oos_candles)

        print(f"\n{sym} DEV: closed={len(dev_result.closed_trades)}, wins={dev_result.win_count}, losses={dev_result.loss_count}, pnl={dev_result.total_pnl:.2f}")
        print(f"{sym} OOS: closed={len(oos_result.closed_trades)}, wins={oos_result.win_count}, losses={oos_result.loss_count}, pnl={oos_result.total_pnl:.2f}")


if __name__ == "__main__":
    asyncio.run(main())