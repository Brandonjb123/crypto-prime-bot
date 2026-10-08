"""Tests for lifecycle expiry calculator."""

from datetime import UTC, datetime

import pytest

from src.signal.lifecycle_expiry_calculator import calculate_expires_at


class TestCalculateExpiresAt:
    def test_basic_next_boundary(self):
        """Created 01:00 → next boundary is 04:00."""
        created = datetime(2026, 10, 8, 1, 0, 0, tzinfo=UTC)
        assert calculate_expires_at(created) == datetime(
            2026, 10, 8, 4, 0, 0, tzinfo=UTC
        )

    def test_exactly_on_boundary(self):
        """Created 04:00:00 → strictly next boundary 08:00."""
        created = datetime(2026, 10, 8, 4, 0, 0, tzinfo=UTC)
        assert calculate_expires_at(created) == datetime(
            2026, 10, 8, 8, 0, 0, tzinfo=UTC
        )

    def test_minimum_window_under_15m(self):
        """Created 03:50 → gap to 04:00 is 10m < 15m → use 08:00."""
        created = datetime(2026, 10, 8, 3, 50, 0, tzinfo=UTC)
        assert calculate_expires_at(created) == datetime(
            2026, 10, 8, 8, 0, 0, tzinfo=UTC
        )

    def test_03_30_keeps_04_00(self):
        """Created 03:30 → gap 30m > 15m → keep 04:00."""
        created = datetime(2026, 10, 8, 3, 30, 0, tzinfo=UTC)
        assert calculate_expires_at(created) == datetime(
            2026, 10, 8, 4, 0, 0, tzinfo=UTC
        )

    def test_03_50_skips_04_00_to_08_00(self):
        """Created 03:50 → gap 10m < 15m → skip to 08:00."""
        created = datetime(2026, 10, 8, 3, 50, 0, tzinfo=UTC)
        assert calculate_expires_at(created) == datetime(
            2026, 10, 8, 8, 0, 0, tzinfo=UTC
        )    

    def test_exactly_15m_window(self):
        """Created 03:45 → gap to 04:00 is exactly 15m → keep 04:00."""
        created = datetime(2026, 10, 8, 3, 45, 0, tzinfo=UTC)
        assert calculate_expires_at(created) == datetime(
            2026, 10, 8, 4, 0, 0, tzinfo=UTC
        )

    def test_just_under_15m(self):
        """Created 03:45:01 → gap 14:59 < 15m → use 08:00."""
        created = datetime(2026, 10, 8, 3, 45, 1, tzinfo=UTC)
        assert calculate_expires_at(created) == datetime(
            2026, 10, 8, 8, 0, 0, tzinfo=UTC
        )

    def test_cross_midnight(self):
        """Created 23:50 → 00:00 next day is 10m → use 04:00 next day."""
        created = datetime(2026, 10, 8, 23, 50, 0, tzinfo=UTC)
        assert calculate_expires_at(created) == datetime(
            2026, 10, 9, 4, 0, 0, tzinfo=UTC
        )

    def test_boundary_at_20(self):
        """Created 20:30 → next boundary 00:00 next day."""
        created = datetime(2026, 10, 8, 20, 30, 0, tzinfo=UTC)
        assert calculate_expires_at(created) == datetime(
            2026, 10, 9, 0, 0, 0, tzinfo=UTC
        )

    def test_midnight_created(self):
        """Created 00:30 → next boundary 04:00."""
        created = datetime(2026, 10, 8, 0, 30, 0, tzinfo=UTC)
        assert calculate_expires_at(created) == datetime(
            2026, 10, 8, 4, 0, 0, tzinfo=UTC
        )

    def test_naive_datetime_raises(self):
        created = datetime(2026, 10, 8, 1, 0, 0)
        with pytest.raises(ValueError, match="timezone-aware"):
            calculate_expires_at(created)