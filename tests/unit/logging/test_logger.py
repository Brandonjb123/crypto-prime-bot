from src.logging.logger import get_logger


class TestLogger:
    def test_get_logger_returns_logger(self):
        logger = get_logger("test_module")
        assert logger is not None

    def test_logger_info_works(self, caplog):
        logger = get_logger("test_info")
        logger.info("test message")
        assert "test message" in caplog.text

    def test_logger_warning_works(self, caplog):
        logger = get_logger("test_warn")
        logger.warning("warning message")
        assert "warning message" in caplog.text