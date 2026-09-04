from datetime import UTC, datetime

import pytest

from src.core.models.telegram import TelegramMessage, TelegramResponse
from src.core.types.enums import TelegramCommand
from src.telegram.bot import TelegramBot

COMMANDS = [
    "/start",
    "/help",
    "/status",
    "/signals",
    "/positions",
    "/portfolio",
    "/history",
    "/trackrecord",
    "/subscribe",
    "/checkout",
    "/terms",
    "/privacy",
    "/risk",
    "/lastsignal",
]


@pytest.mark.parametrize("raw", COMMANDS)
def test_parse_command_does_not_return_none(raw):
    bot = TelegramBot()
    command = bot._parse_command(raw)
    assert command is not None, f"{raw} tidak dikenali"


@pytest.mark.parametrize("raw", COMMANDS)
def test_route_command_returns_telegram_response(raw):
    bot = TelegramBot()
    command = bot._parse_command(raw)
    if command == TelegramCommand.START:
        # START ditangani khusus, tidak lewat router
        return

    msg = TelegramMessage(
        chat_id="1",
        command=command,
        text=raw,
        timestamp=datetime.now(UTC),
    )
    resp = bot.router.route(msg, {})
    assert isinstance(resp, TelegramResponse), f"{raw} gagal di-route"