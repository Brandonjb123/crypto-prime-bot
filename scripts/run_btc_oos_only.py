"""BTC OOS-only validation — 250 observations, tanpa DEV."""

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
    symbol = "BTC"
    print("BTC OOS-only validation...")

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
    oos_candles = candles[split_idx:]

    print(f"OOS observations: {len(oos_candles)}")

    result = await runner.run_asset(symbol, oos_candles)

    print("\n=== OOS RESULT ===")
    print(f"Total observations: {len(oos_candles)}")
    print(f"Valid decisions: {result.valid_decision_count}")
    print(f"AI unavailable: {result.ai_unavailable_count}")
    print(f"Genuine WAIT: {result.wait_signals}")
    print(f"BUY: {result.buy_signals}")
    print(f"SELL: {result.sell_signals}")
    print(f"Closed trades: {len(result.closed_trades)}")
    print(f"Wins: {result.win_count}")
    print(f"Losses: {result.loss_count}")
    print(f"PnL: {result.total_pnl:.2f}")
    print(f"Win rate: {(result.win_count / len(result.closed_trades) * 100) if result.closed_trades else 0.0:.2f}%")


if __name__ == "__main__":
    asyncio.run(main())