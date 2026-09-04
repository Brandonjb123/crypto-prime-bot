"""Controlled Groq validation — jalankan satu aset dengan OOS split."""

import asyncio
import sys
from pathlib import Path

import httpx

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.bootstrap.container import Container  # noqa: E402
from src.simulation.historical_simulation import HistoricalSimulationRunner  # noqa: E402

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
    symbol = sys.argv[1] if len(sys.argv) > 1 else "BTC"
    print(f"Controlled Groq validation for {symbol}...")

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

    candles = await fetch_klines(symbol)
    split_idx = int(len(candles) * 0.7)
    dev_candles = candles[:split_idx]
    oos_candles = candles[split_idx:]

    # Development period
    print("DEV period...")
    dev_result = await runner.run_asset(symbol, dev_candles)
    _print_result(symbol, dev_result, "DEV")

    # Out-of-sample period
    print("OOS period...")
    oos_result = await runner.run_asset(symbol, oos_candles)
    _print_result(symbol, oos_result, "OOS")


def _print_result(symbol: str, result, label: str) -> None:
    print(f"{label} {symbol}: "
          f"closed={len(result.closed_trades)}, "
          f"wins={result.win_count}, losses={result.loss_count}, "
          f"pnl={result.total_pnl:.2f}")
    print(f"  valid_decisions={result.valid_decision_count}, "
          f"ai_unavailable={result.ai_unavailable_count}, "
          f"buys={result.buy_signals}, sells={result.sell_signals}, "
          f"waits={result.wait_signals}")


if __name__ == "__main__":
    asyncio.run(main())