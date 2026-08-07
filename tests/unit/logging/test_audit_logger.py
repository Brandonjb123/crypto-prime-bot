from src.core.types.enums import AuditEventType
from src.logging.audit_logger import AuditLogger


class TestAuditLogger:
    def test_record_event(self):
        al = AuditLogger()
        al.record(AuditEventType.PIPELINE_START, "BTC analysis started")
        records = al.get_records()
        assert len(records) == 1
        assert records[0].event_type == AuditEventType.PIPELINE_START

    def test_multiple_records(self):
        al = AuditLogger()
        al.record(AuditEventType.ORDER_CREATED, "Order placed")
        al.record(AuditEventType.POSITION_OPENED, "Position opened")
        assert len(al.get_records()) == 2

    def test_get_records_returns_copy(self):
        al = AuditLogger()
        al.record(AuditEventType.PIPELINE_COMPLETE, "done")
        records = al.get_records()
        records.clear()
        assert len(al.get_records()) == 1  # original unchanged

    def test_record_message_content(self):
        al = AuditLogger()
        al.record(AuditEventType.PIPELINE_FAILED, "timeout error")
        record = al.get_records()[0]
        assert "timeout error" in record.message