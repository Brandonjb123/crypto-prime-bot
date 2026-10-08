"""Lifecycle expiry calculator — UTC-aligned 4H boundary with min 15m window."""

from datetime import datetime, timedelta

BOUNDARY_INTERVAL_HOURS = 4
MIN_WINDOW = timedelta(minutes=15)


def calculate_expires_at(created_at: datetime) -> datetime:
    """Calculate expires_at for a SignalLifecycle.

    Rules:
    - expires_at = next UTC-aligned 4H calendar boundary
      (00:00, 04:00, 08:00, 12:00, 16:00, 20:00 UTC)
    - If the next boundary is <15 minutes away from created_at,
      use the following boundary instead.
    - Always returns timezone-aware datetime (UTC).
    - Raises ValueError if created_at is not timezone-aware.
    """
    if created_at.tzinfo is None:
        raise ValueError("created_at must be timezone-aware (UTC)")

    base = created_at.replace(minute=0, second=0, microsecond=0)
    next_boundary_hour = (
        (base.hour // BOUNDARY_INTERVAL_HOURS) + 1
    ) * BOUNDARY_INTERVAL_HOURS

    if next_boundary_hour >= 24:
        next_boundary = base.replace(hour=0) + timedelta(days=1)
    else:
        next_boundary = base.replace(hour=next_boundary_hour)

    if next_boundary - created_at < MIN_WINDOW:
        next_boundary += timedelta(hours=BOUNDARY_INTERVAL_HOURS)

    return next_boundary