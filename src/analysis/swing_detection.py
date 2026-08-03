"""Utility functions untuk mendeteksi swing high dan swing low."""

from src.core.models.candle import Candle


def find_swing_high(candles: list[Candle], window: int = 3) -> float | None:
    """Cari swing high terbaru: high tertinggi di window N-N."""
    for i in range(len(candles) - 1 - window, window - 1, -1):
        current_high = candles[i].high
        is_swing = True
        for j in range(i - window, i + window + 1):
            if j != i and candles[j].high >= current_high:
                is_swing = False
                break
        if is_swing:
            return current_high
    return None


def find_swing_low(candles: list[Candle], window: int = 3) -> float | None:
    """Cari swing low terbaru: low terendah di window N-N."""
    for i in range(len(candles) - 1 - window, window - 1, -1):
        current_low = candles[i].low
        is_swing = True
        for j in range(i - window, i + window + 1):
            if j != i and candles[j].low <= current_low:
                is_swing = False
                break
        if is_swing:
            return current_low
    return None