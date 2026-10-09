from src.notification.recipient_config import parse_recipient_ids


class TestParseRecipientIds:
    def test_empty_string_returns_empty(self):
        assert parse_recipient_ids("") == []

    def test_none_returns_empty(self):
        assert parse_recipient_ids(None) == []

    def test_whitespace_only_returns_empty(self):
        assert parse_recipient_ids("  ,  ,  ") == []

    def test_single_id(self):
        assert parse_recipient_ids("123456") == ["123456"]

    def test_multiple_ids(self):
        assert parse_recipient_ids("123, 456 , 789") == ["123", "456", "789"]

    def test_duplicate_ids_deduplicated_order_preserved(self):
        assert parse_recipient_ids("100, 200, 100, 300, 200") == ["100", "200", "300"]

    def test_invalid_entry_disables_fanout(self):
        assert parse_recipient_ids("123,abc,456") == []

    def test_over_limit_disables_fanout(self):
        ids = ",".join([str(i) for i in range(1, 22)])  # 21 IDs
        assert parse_recipient_ids(ids) == []

    def test_exactly_20_ids_ok(self):
        ids = ",".join([str(i) for i in range(1, 21)])
        assert len(parse_recipient_ids(ids)) == 20