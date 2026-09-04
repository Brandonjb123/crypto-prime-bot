from src.telegram.command_handler import (
    help_handler,
    history_handler,
    start_handler,
    subscribe_handler,
    trackrecord_handler,
)


def test_start_contains_disclaimer():
    resp = start_handler(None, {})
    assert "EARLY TRACK RECORD" in resp.text


def test_help_contains_required_commands():
    resp = help_handler(None, {})
    for cmd in [
        "/signals",
        "/positions",
        "/portfolio",
        "/history",
        "/trackrecord",
        "/subscribe",
        "/terms",
        "/privacy",
        "/risk",
    ]:
        assert cmd in resp.text


def test_history_is_customer_facing():
    resp = history_handler(None, {})
    assert "No reasoning" not in resp.text
    assert "debug" not in resp.text.lower()


def test_trackrecord_contains_disclaimer():
    resp = trackrecord_handler(None, {})
    assert "EARLY TRACK RECORD" in resp.text


def test_subscribe_contains_disclaimer_and_cta():
    resp = subscribe_handler(None, {})
    assert "EARLY TRACK RECORD" in resp.text
    assert "/checkout" in resp.text