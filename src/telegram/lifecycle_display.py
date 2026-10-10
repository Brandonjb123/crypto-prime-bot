"""Lifecycle display state resolution for Telegram surfaces (H3.2).

Converts raw lifecycle query results into conservative display states:
- ACTIVE  : snapshot ACTIVE + lifecycle row ACTIVE
- EXPIRED : lifecycle row EXPIRED (regardless of snapshot)
- LEGACY  : no lifecycle row for that signal
- UNKNOWN : query failed, unrecognized state, or cannot establish trust

Never silently maps query failure to LEGACY.
"""

from uuid import UUID

from loguru import logger

from src.storage.repositories.signal_repository import SignalRepository

LIFECYCLE_ACTIVE = "ACTIVE"
LIFECYCLE_EXPIRED = "EXPIRED"
LIFECYCLE_LEGACY = "LEGACY"
LIFECYCLE_UNKNOWN = "UNKNOWN"

_VALID_RAW_STATES = {LIFECYCLE_ACTIVE, LIFECYCLE_EXPIRED}


def resolve_lifecycle_states(
    repo: SignalRepository,
    signal_ids: list[UUID],
) -> dict[UUID, str]:
    """Bulk-resolve lifecycle display state for given signal IDs.

    Returns mapping signal_id -> one of ACTIVE / EXPIRED / LEGACY / UNKNOWN.
    On query failure: all UNKNOWN (never fallback to LEGACY or ACTIVE).
    """
    if not signal_ids:
        return {}

    # Dedup while preserving deterministic output
    unique_ids: list[UUID] = []
    seen: set[UUID] = set()
    for sid in signal_ids:
        if sid not in seen:
            seen.add(sid)
            unique_ids.append(sid)

    try:
        raw = repo.get_lifecycle_states(unique_ids)
    except Exception as e:
        logger.warning(
            f"[lifecycle_display] lifecycle state lookup failed: {e} — "
            f"falling back to UNKNOWN for {len(unique_ids)} signal(s)"
        )
        return {sid: LIFECYCLE_UNKNOWN for sid in unique_ids}

    result: dict[UUID, str] = {}
    for sid in unique_ids:
        if sid not in raw:
            result[sid] = LIFECYCLE_LEGACY
        elif raw[sid] in _VALID_RAW_STATES:
            result[sid] = raw[sid]
        else:
            # Unrecognized state from DB — conservative
            logger.warning(
                f"[lifecycle_display] unrecognized lifecycle state "
                f"'{raw[sid]}' for {sid} — treating as UNKNOWN"
            )
            result[sid] = LIFECYCLE_UNKNOWN
    return result