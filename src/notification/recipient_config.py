"""Recipient configuration parser + validator (C0.0.4A).

Parses comma-separated Telegram IDs from config. Validates constraints:
- Max 20 unique IDs
- Non-numeric entries → invalid config → fan-out disabled
- Duplicates deduplicated (preserve order)
- Empty config → no recipients (valid, fan-out skipped)

Invalid config: return empty list + ERROR log. Do not partial-accept.
"""

from loguru import logger

MAX_RECIPIENTS = 20


def parse_recipient_ids(raw: str) -> list[str]:
    """Parse comma-separated recipient IDs. Return [] on invalid config."""
    if raw is None or raw.strip() == "":
        logger.info("[outbox] NOTIFICATION_RECIPIENT_IDS empty — fan-out disabled")
        return []

    parts = [p.strip() for p in raw.split(",") if p.strip()]
    if not parts:
        logger.info("[outbox] NOTIFICATION_RECIPIENT_IDS whitespace-only — disabled")
        return []

    # Validate: all entries must be non-empty strings (Telegram IDs are str-convertible)
    invalid = [p for p in parts if not p.replace("-", "").isdigit()]
    if invalid:
        logger.error(
            f"[outbox] Invalid NOTIFICATION_RECIPIENT_IDS entries: {invalid} — "
            f"fan-out disabled (no partial accept)"
        )
        return []

    # Dedup while preserving order
    seen = set()
    unique: list[str] = []
    for p in parts:
        if p not in seen:
            seen.add(p)
            unique.append(p)

    if len(unique) > MAX_RECIPIENTS:
        logger.error(
            f"[outbox] NOTIFICATION_RECIPIENT_IDS exceeds max "
            f"({len(unique)} > {MAX_RECIPIENTS}) — fan-out disabled"
        )
        return []

    logger.info(f"[outbox] {len(unique)} recipients configured")
    return unique