from src.telegram.formatter import format_help, format_status


class TestFormatter:
    def test_format_status(self):
        text = format_status("RUNNING", "IDLE")
        assert "RUNNING" in text

    def test_format_help(self):
        text = format_help()
        assert "/status" in text
