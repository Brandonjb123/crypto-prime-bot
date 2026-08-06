from datetime import datetime, UTC
from src.core.models.backtest import HistoricalCandle
from src.backtest.candle_replay import CandleReplay


def make_candle(ts, close):
    return HistoricalCandle(timestamp=ts, symbol="BTCUSDT", timeframe="4h", open=close-1, high=close+2, low=close-2, close=close, volume=100.0)


class TestCandleReplay:
    def test_replay_order(self):
        c1 = make_candle(datetime(2026,1,1,0,0,0,tzinfo=UTC), 100.0)
        c2 = make_candle(datetime(2026,1,1,4,0,0,tzinfo=UTC), 110.0)
        c3 = make_candle(datetime(2026,1,1,2,0,0,tzinfo=UTC), 105.0)  # out of order
        replay = CandleReplay()
        result = replay.replay([c1, c2, c3])
        assert result[0].timestamp < result[1].timestamp < result[2].timestamp

    def test_empty_candles(self):
        replay = CandleReplay()
        assert replay.replay([]) == []

    def test_deterministic(self):
        candles = [make_candle(datetime(2026,1,1,i*4,0,0,tzinfo=UTC), 100.0+i) for i in range(5)]
        replay = CandleReplay()
        r1 = replay.replay(candles)
        r2 = replay.replay(candles)
        assert r1 == r2