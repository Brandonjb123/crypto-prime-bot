"""Phase B keyboard tests — additive navigation menus."""

from src.telegram.keyboards import (
    BACK_MENU,
    HISTORY_MENU,
    MAIN_MENU,
    PORTFOLIO_MENU,
    POSITIONS_MENU,
    SIGNALS_MENU,
    TRACKRECORD_MENU,
)


def _all_callback_data(keyboard) -> list[str]:
    """Flatten all callback_data from an InlineKeyboardMarkup."""
    out = []
    for row in keyboard.inline_keyboard:
        for btn in row:
            if btn.callback_data:
                out.append(btn.callback_data)
    return out


class TestPortfolioMenu:
    def test_portfolio_menu_has_5_buttons(self) -> None:
        assert len(_all_callback_data(PORTFOLIO_MENU)) == 5

    def test_portfolio_menu_correct_callbacks(self) -> None:
        callbacks = _all_callback_data(PORTFOLIO_MENU)
        assert "refresh_portfolio" in callbacks
        assert "menu_positions" in callbacks
        assert "menu_history" in callbacks
        assert "menu_trackrecord" in callbacks
        assert "menu_back" in callbacks

    def test_portfolio_menu_no_duplicates(self) -> None:
        callbacks = _all_callback_data(PORTFOLIO_MENU)
        assert len(callbacks) == len(set(callbacks))


class TestPositionsMenu:
    def test_positions_menu_callbacks(self) -> None:
        callbacks = _all_callback_data(POSITIONS_MENU)
        assert "refresh_positions" in callbacks
        assert "menu_back" in callbacks

    def test_positions_menu_no_duplicates(self) -> None:
        callbacks = _all_callback_data(POSITIONS_MENU)
        assert len(callbacks) == len(set(callbacks))


class TestHistoryMenu:
    def test_history_menu_callbacks(self) -> None:
        callbacks = _all_callback_data(HISTORY_MENU)
        assert "refresh_history" in callbacks
        assert "menu_trackrecord" in callbacks
        assert "menu_back" in callbacks

    def test_history_menu_no_duplicates(self) -> None:
        callbacks = _all_callback_data(HISTORY_MENU)
        assert len(callbacks) == len(set(callbacks))


class TestTrackRecordMenu:
    def test_trackrecord_menu_callbacks(self) -> None:
        callbacks = _all_callback_data(TRACKRECORD_MENU)
        assert "refresh_trackrecord" in callbacks
        assert "menu_history" in callbacks
        assert "menu_back" in callbacks

    def test_trackrecord_menu_no_duplicates(self) -> None:
        callbacks = _all_callback_data(TRACKRECORD_MENU)
        assert len(callbacks) == len(set(callbacks))


class TestExistingMenusUnchanged:
    def test_main_menu_has_8_buttons(self) -> None:
        assert len(_all_callback_data(MAIN_MENU)) == 8

    def test_main_menu_expected_callbacks(self) -> None:
        callbacks = _all_callback_data(MAIN_MENU)
        for expected in [
            "menu_signals",
            "menu_portfolio",
            "menu_positions",
            "menu_history",
            "menu_trackrecord",
            "menu_subscribe",
            "menu_help",
            "menu_status",
        ]:
            assert expected in callbacks

    def test_signals_menu_unchanged(self) -> None:
        callbacks = _all_callback_data(SIGNALS_MENU)
        assert "refresh_signals" in callbacks
        assert "menu_back" in callbacks
        assert len(callbacks) == 2

    def test_back_menu_unchanged(self) -> None:
        callbacks = _all_callback_data(BACK_MENU)
        assert callbacks == ["menu_back"]


class TestNoDuplicateAcrossMenus:
    def test_no_callback_data_duplicated_across_menus(self) -> None:
        """Setiap callback_data unik di dalam keyboard. Duplikat di keyboard
        berbeda (mis. menu_back) memang boleh, tapi di dalam 1 keyboard tidak."""
        all_menus = [
            MAIN_MENU,
            BACK_MENU,
            SIGNALS_MENU,
            PORTFOLIO_MENU,
            POSITIONS_MENU,
            HISTORY_MENU,
            TRACKRECORD_MENU,
        ]
        for menu in all_menus:
            callbacks = _all_callback_data(menu)
            assert len(callbacks) == len(set(callbacks)), (
                f"Duplicate callback in menu: {callbacks}"
            )