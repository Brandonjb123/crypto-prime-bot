"""Lifecycle display state resolution for Telegram surfaces (H3.2 Revision 2).

State semantics:
- ACTIVE  : lookup succeeded, row ACTIVE, expires_at is known & now < expires_at
- EXPIRED : row EXPIRED, OR row ACTIVE but expires_at is known & now >= expires_at
- LEGACY  : lookup succeeded, absent, and signal.created_at is timezone-aware
            and strictly before LIFECYCLE_EPOCH_UTC
- RECENT  : lookup succeeded, absent, and signal.created_at is timezone-aware
            and >= LIFECYCLE_EPOCH_UTC
- UNKNOWN : lookup failed, unrecognized state, or timezone ambiguity
            (naive datetime) — conservative fallback, never LEGACY

R1 compliance: naive datetime is NEVER assumed UTC. Naive created_at cannot
prove pre-epoch → UNKNOWN (not LEGACY). Naive expires_at cannot prove
not-yet-expired → UNKNOWN.
"""

from datetime import UTC, datetime
from uuid import UUID

from loguru import logger

from src.core.models.lifecycle_lookup import LifecycleLookupResult
from src.core.ports.lifecycle_read import LifecycleReadPort

LIFECYCLE_EPOCH_UTC = datetime(2026, 10, 9, 12, 40, 26, tzinfo=UTC)

LIFECYCLE_ACTIVE = "ACTIVE"
LIFECYCLE_EXPIRED = "EXPIRED"
LIFECYCLE_LEGACY = "LEGACY"
LIFECYCLE_RECENT = "RECENT"
LIFECYCLE_UNKNOWN = "UNKNOWN"

_VALID_RAW_STATES = {LIFECYCLE_ACTIVE, LIFECYCLE_EXPIRED}


def _is_tz_aware(dt: datetime) -> bool:
    return dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None


def _classify_one(signal, result: LifecycleLookupResult, now_utc: datetime) -> str:
    signal_id = signal.signal_id

    # B2: defense-in-depth — reject any id present in more than one bucket
    in_found = signal_id in result.found
    in_absent = signal_id in result.absent
    in_failed = signal_id in result.failed
    bucket_count = int(in_found) + int(in_absent) + int(in_failed)
    if bucket_count > 1:
        logger.warning(
            f"[lifecycle_display] signal {signal_id} present in "
            f"multiple buckets (found={in_found}, absent={in_absent}, "
            f"failed={in_failed}) — treating as UNKNOWN"
        )
        return LIFECYCLE_UNKNOWN

    if signal_id in result.failed:
        return LIFECYCLE_UNKNOWN

    rec = result.found.get(signal_id)
    if rec is not None:
        if rec.status not in _VALID_RAW_STATES:
            logger.warning(
                f"[lifecycle_display] unrecognized lifecycle state "
                f"'{rec.status}' for {signal_id} — treating as UNKNOWN"
            )
            return LIFECYCLE_UNKNOWN
        if rec.status == LIFECYCLE_EXPIRED:
            return LIFECYCLE_EXPIRED
        if rec.status == LIFECYCLE_ACTIVE:
            if rec.expires_at is None:
                logger.warning(
                    f"[lifecycle_display] ACTIVE record for {signal_id} "
                    f"missing expires_at — treating as UNKNOWN"
                )
                return LIFECYCLE_UNKNOWN
            if not _is_tz_aware(rec.expires_at):
                logger.warning(
                    f"[lifecycle_display] naive expires_at for {signal_id} — "
                    f"cannot safely compare, treating as UNKNOWN"
                )
                return LIFECYCLE_UNKNOWN
            if now_utc >= rec.expires_at:
                return LIFECYCLE_EXPIRED
            return LIFECYCLE_ACTIVE

    if signal_id in result.absent:
        created_at = getattr(signal, "created_at", None)
        if created_at is None:
            logger.warning(
                f"[lifecycle_display] signal {signal_id} has no created_at "
                f"— treating as UNKNOWN"
            )
            return LIFECYCLE_UNKNOWN
        if not _is_tz_aware(created_at):
            logger.warning(
                f"[lifecycle_display] signal {signal_id} has naive created_at "
                f"— cannot prove pre-epoch, treating as UNKNOWN"
            )
            return LIFECYCLE_UNKNOWN
        if created_at < LIFECYCLE_EPOCH_UTC:
            return LIFECYCLE_LEGACY
        return LIFECYCLE_RECENT

    logger.warning(
        f"[lifecycle_display] signal {signal_id} not in "
        f"found/absent/failed — treating as UNKNOWN"
    )
    return LIFECYCLE_UNKNOWN


def resolve_lifecycle_states(
    repo: LifecycleReadPort,
    signals: list,
    now_utc: datetime,
) -> dict[UUID, str]:
    """Resolve display state for given signal objects.

    - `repo` must be a SignalLifecycleRepository (has .get_lifecycle_lookup).
    - Only signals with status == 'ACTIVE' are looked up.
      SKIPPED / INVALID are excluded (baseline display preserved).
    - `now_utc` must be timezone-aware; single timestamp per render.

    Returns mapping signal_id -> ACTIVE / EXPIRED / LEGACY / RECENT / UNKNOWN.
    On lookup failure: all UNKNOWN.
    """
    if not signals:
        return {}

    if not _is_tz_aware(now_utc):
        logger.warning(
            "[lifecycle_display] now_utc is naive — refusing to classify"
        )
        return {}

    candidates = [
        s
        for s in signals
        if getattr(s, "status", None) == "ACTIVE"
        and getattr(s, "signal_id", None) is not None
    ]
    if not candidates:
        return {}

    seen: set[UUID] = set()
    unique: list = []
    for s in candidates:
        if s.signal_id not in seen:
            seen.add(s.signal_id)
            unique.append(s)

    try:
        result = repo.get_lifecycle_lookup([s.signal_id for s in unique])
    except Exception as e:
        logger.warning(
            f"[lifecycle_display] lifecycle lookup failed: {e} — "
            f"falling back to UNKNOWN for {len(unique)} signal(s)"
        )
        return {s.signal_id: LIFECYCLE_UNKNOWN for s in unique}

    return {s.signal_id: _classify_one(s, result, now_utc) for s in unique}