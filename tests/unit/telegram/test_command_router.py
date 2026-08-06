from datetime import datetime, UTC
from src.core.models.telegram import TelegramMessage, TelegramResponse
from src.core.types.enums import TelegramCommand, TelegramResponseType
from src.telegram.command_router import CommandRouter


class TestCommandRouter:
    def test_register_and_route(self):
        router = CommandRouter()
        router.register(TelegramCommand.STATUS, lambda msg: TelegramResponse(
            response_type=TelegramResponseType.TEXT, text="OK", timestamp=datetime.now(UTC)))
        msg = TelegramMessage(chat_id="123", command=TelegramCommand.STATUS, timestamp=datetime.now(UTC))
        resp = router.route(msg)
        assert resp.text == "OK"

    def test_unknown_command(self):
        router = CommandRouter()
        msg = TelegramMessage(chat_id="123", command=TelegramCommand.STATUS, timestamp=datetime.now(UTC))
        resp = router.route(msg)
        assert resp.response_type == TelegramResponseType.UNKNOWN

    def test_multiple_commands(self):
        router = CommandRouter()
        router.register(TelegramCommand.HELP, lambda msg: TelegramResponse(
            response_type=TelegramResponseType.TEXT, text="Help", timestamp=datetime.now(UTC)))
        router.register(TelegramCommand.STATUS, lambda msg: TelegramResponse(
            response_type=TelegramResponseType.TEXT, text="Status", timestamp=datetime.now(UTC)))
        assert router.route(TelegramMessage(chat_id="1", command=TelegramCommand.HELP, timestamp=datetime.now(UTC))).text == "Help"
        assert router.route(TelegramMessage(chat_id="1", command=TelegramCommand.STATUS, timestamp=datetime.now(UTC))).text == "Status"

    def test_deterministic(self):
        router = CommandRouter()
        router.register(TelegramCommand.STATUS, lambda msg: TelegramResponse(
            response_type=TelegramResponseType.TEXT, text="OK", timestamp=datetime.now(UTC)))
        msg = TelegramMessage(chat_id="123", command=TelegramCommand.STATUS, timestamp=datetime.now(UTC))
        r1 = router.route(msg)
        r2 = router.route(msg)
        assert r1.text == r2.text