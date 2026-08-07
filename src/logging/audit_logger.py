"""Audit Logger — record event audit."""

from datetime import datetime, UTC
from src.core.models.audit import AuditRecord
from src.core.types.enums import AuditEventType
from src.logging.logger import get_logger

logger = get_logger("audit")


class AuditLogger:
    def __init__(self) -> None:
        self.records: list[AuditRecord] = []

    def record(self, event_type: AuditEventType, message: str) -> None:
        record = AuditRecord(
            event_type=event_type,
            message=message,
            timestamp=datetime.now(UTC),
        )
        self.records.append(record)
        logger.info(f"[AUDIT] {event_type.value}: {message}")

    def get_records(self) -> list[AuditRecord]:
        return self.records.copy()