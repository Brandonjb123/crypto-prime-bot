"""Tests for zone calculation with RR-based clipping (C0.0.2)."""

from src.pipeline.pipeline_runner import (
    MIN_EFFECTIVE_RR,
    ZONE_HALF_WIDTH_ATR,
    _calculate_zone_with_clipping,
)


class TestFullRangeNoClip:
    def test_full_range_rr_above_threshold(self):
        """Setup dengan RR worst-case >= 2.5 tanpa clipping."""
        # Entry 100, SL 95, TP 130, ATR 4
        # zone: [99, 101]
        # BUY worst = 101, risk = 6, reward = 29, RR ≈ 4.83
        zone_low, zone_high, rr = _calculate_zone_with_clipping(
            entry_price=100.0,
            stop_loss=95.0,
            take_profit=130.0,
            atr=4.0,
            side="BUY",
        )
        assert zone_low == 99.0
        assert zone_high == 101.0
        assert rr is not None
        assert rr >= MIN_EFFECTIVE_RR


class TestLongClipping:
    def test_long_clip_high_side(self):
        """Baseline RR 1:3 → worst-case ~2.43 → clip zone_high."""
        # Entry 100, ATR 10, SL = 85 (1.5 ATR), TP = 145 (4.5 ATR)
        # Full zone: [97.5, 102.5]
        # Worst BUY = 102.5, risk = 17.5, reward = 42.5, RR ≈ 2.428
        # d_max = (45 - 2.5*15)/3.5 = 7.5/3.5 ≈ 2.142857
        zone_low, zone_high, rr = _calculate_zone_with_clipping(
            entry_price=100.0,
            stop_loss=85.0,
            take_profit=145.0,
            atr=10.0,
            side="BUY",
        )
        # zone_low (safe side) unchanged
        assert zone_low == 100.0 - ZONE_HALF_WIDTH_ATR * 10.0
        # zone_high clipped below original
        assert zone_high < 100.0 + ZONE_HALF_WIDTH_ATR * 10.0
        assert zone_high > 100.0
        assert rr is not None
        assert rr >= MIN_EFFECTIVE_RR
        assert abs(rr - MIN_EFFECTIVE_RR) < 1e-6


class TestShortClipping:
    def test_short_clip_low_side(self):
        """SHORT: clip zone_low (unsafe side)."""
        # Entry 100, ATR 10, SL = 115, TP = 55
        zone_low, zone_high, rr = _calculate_zone_with_clipping(
            entry_price=100.0,
            stop_loss=115.0,
            take_profit=55.0,
            atr=10.0,
            side="SELL",
        )
        # zone_high (safe side) unchanged
        assert zone_high == 100.0 + ZONE_HALF_WIDTH_ATR * 10.0
        # zone_low clipped above original
        assert zone_low > 100.0 - ZONE_HALF_WIDTH_ATR * 10.0
        assert zone_low < 100.0
        assert rr is not None
        assert rr >= MIN_EFFECTIVE_RR
        assert abs(rr - MIN_EFFECTIVE_RR) < 1e-6


class TestRRBoundary:
    def test_exact_rr_boundary_no_clip(self):
        """RR exactly 2.5 at full zone boundary → no clip."""
        # Entry 100, SL 85 (risk 15), zone_high = 102.5
        # Untuk RR = 2.5: reward = 17.5 * 2.5 = 43.75, TP = 102.5 + 43.75 = 146.25
        zone_low, zone_high, rr = _calculate_zone_with_clipping(
            entry_price=100.0,
            stop_loss=85.0,
            take_profit=146.25,
            atr=10.0,
            side="BUY",
        )
        assert zone_low == 97.5
        assert zone_high == 102.5
        assert rr is not None
        assert abs(rr - MIN_EFFECTIVE_RR) < 1e-9


class TestPostClippingValidation:
    def test_after_clip_rr_at_least_2_5(self):
        zone_low, zone_high, rr = _calculate_zone_with_clipping(
            entry_price=100.0,
            stop_loss=85.0,
            take_profit=145.0,
            atr=10.0,
            side="BUY",
        )
        assert rr is not None
        assert rr >= MIN_EFFECTIVE_RR


class TestDegenerate:
    def test_impossible_rr_returns_none(self):
        """TP sangat dekat → RR tidak bisa >= 2.5 bahkan dengan clipping."""
        zone_low, zone_high, rr = _calculate_zone_with_clipping(
            entry_price=100.0,
            stop_loss=85.0,
            take_profit=105.0,
            atr=10.0,
            side="BUY",
        )
        assert rr is None

    def test_zero_atr_returns_none_no_fallback_zone(self):
        """ATR=0 → no valid zone → all None (no artificial fallback)."""
        zone_low, zone_high, rr = _calculate_zone_with_clipping(
            entry_price=100.0,
            stop_loss=85.0,
            take_profit=145.0,
            atr=0.0,
            side="BUY",
        )
        assert zone_low is None
        assert zone_high is None
        assert rr is None

    def test_negative_atr_returns_none(self):
        """ATR<0 → invalid → all None."""
        zone_low, zone_high, rr = _calculate_zone_with_clipping(
            entry_price=100.0,
            stop_loss=85.0,
            take_profit=145.0,
            atr=-5.0,
            side="BUY",
        )
        assert zone_low is None
        assert zone_high is None
        assert rr is None

    def test_zero_atr_short_returns_none(self):
        zone_low, zone_high, rr = _calculate_zone_with_clipping(
            entry_price=100.0,
            stop_loss=115.0,
            take_profit=55.0,
            atr=0.0,
            side="SELL",
        )
        assert zone_low is None
        assert zone_high is None
        assert rr is None