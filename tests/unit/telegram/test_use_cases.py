"""Tests untuk src.telegram.use_cases.

Synthetic fixtures, tidak bergantung pada dataset production.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from src.core.models.portfolio_state import PortfolioState
from src.core.models.position import Position
from src.core.models.trading_signal import TradingSignal
from src.core.types.enums import (
    PositionCloseReason,
    PositionStatus,
    Side,
)
from src.telegram.use_cases import (
    TrackRecordSummary,
    read_history,
    read_last_signal,
    read_latest_signals,
    read_portfolio,
    read_positions,
    read_trackrecord,
)

# ---------- fixtures ----------


def _make_position(
    status: PositionStatus = PositionStatus.OPEN,
    realized_pnl: float = 0.0,
    symbol: str = "BTC",
) -> Position:
    now = datetime.now(UTC)
    is_closed = status == PositionStatus.CLOSED
    return Position(
        position_id=uuid4(),
        execution_id=uuid4(),
        order_id=uuid4(),
        signal_id=uuid4(),
        symbol=symbol,
        side=Side.LONG,
        status=status,
        entry_price=50000.0,
        stop_loss=49000.0,
        take_profit=52000.0,
        tp1_price=51000.0,
        tp2_price=52000.0,
        position_size=0.01,
        opened_at=now,
        closed_at=now if is_closed else None,
        close_reason=(
            PositionCloseReason.MANUAL
            if is_closed
            else PositionCloseReason.NONE
        ),
        last_price=50000.0,
        last_updated=now,
        realized_pnl=realized_pnl,
    )


def _make_state() -> PortfolioState:
    return PortfolioState(
        account_balance=10000.0,
        equity=10100.0,
        realized_pnl=100.0,
        unrealized_pnl=0.0,
        total_pnl=100.0,
        open_positions=1,
        closed_positions=2,
        peak_equity=10100.0,
        drawdown=0.0,
        drawdown_percent=0.0,
        timestamp=datetime.now(UTC),
    )


def _make_signal(symbol: str = "BTC", status: str = "ACTIVE") -> TradingSignal:
    return TradingSignal(
        signal_id=uuid4(),
        symbol=symbol,
        side="BUY",
        status=status,
        entry_price=50000.0,
        stop_loss=49000.0,
        take_profit=52000.0,
        take_profit_1=51000.0,
        take_profit_2=52000.0,
        position_size=0.01,
        risk_percent=1.0,
        confidence=80,
        risk_level="MEDIUM",
        reasoning=["r1", "r2"],
        created_at=datetime.now(UTC),
    )


class _FakeSignalRepo:
    """Minimal stub matching SignalRepository read API."""

    def __init__(
        self,
        latest_by_symbol: dict | None = None,
        history: list | None = None,
    ) -> None:
        self._latest = latest_by_symbol or {}
        self._history = list(history or [])

    def latest_by_symbol(self, symbol: str) -> TradingSignal | None:
        return self._latest.get(symbol)

    def history(
        self,
        symbol: str | None = None,
        since: datetime | None = None,
    ) -> list[TradingSignal]:
        return list(self._history)


# ---------- read_portfolio ----------


class TestReadPortfolio:
    def test_read_portfolio_from_ctx(self) -> None:
        state = _make_state()
        ctx = {"portfolio_snapshot": state}
        assert read_portfolio(ctx) is state

    def test_read_portfolio_none_ctx(self) -> None:
        assert read_portfolio(None) is None

    def test_read_portfolio_missing_key(self) -> None:
        assert read_portfolio({}) is None


# ---------- read_positions ----------


class TestReadPositions:
    def test_read_positions_from_ctx(self) -> None:
        p1 = _make_position()
        p2 = _make_position(symbol="ETH")
        ctx = {"positions": [p1, p2]}
        result = read_positions(ctx)
        assert len(result) == 2
        assert result[0] is p1
        assert result[1] is p2

    def test_read_positions_none_ctx(self) -> None:
        assert read_positions(None) == []

    def test_read_positions_missing_key(self) -> None:
        assert read_positions({}) == []

    def test_read_positions_returns_copy(self) -> None:
        """Appending ke hasil tidak mengubah ctx."""
        p1 = _make_position()
        ctx = {"positions": [p1]}
        result = read_positions(ctx)
        result.append(_make_position())
        assert len(ctx["positions"]) == 1


# ---------- read_history ----------


class TestReadHistory:
    def test_read_history_from_ctx(self) -> None:
        c1 = _make_position(status=PositionStatus.CLOSED, realized_pnl=100.0)
        c2 = _make_position(status=PositionStatus.CLOSED, realized_pnl=-50.0)
        ctx = {"closed_positions": [c1, c2]}
        result = read_history(ctx)
        assert len(result) == 2

    def test_read_history_none_ctx(self) -> None:
        assert read_history(None) == []

    def test_read_history_missing_key(self) -> None:
        assert read_history({}) == []


# ---------- read_trackrecord ----------


class TestReadTrackRecord:
    def test_read_trackrecord_derivations(self) -> None:
        positions = [
            _make_position(status=PositionStatus.CLOSED, realized_pnl=100.0),
            _make_position(status=PositionStatus.CLOSED, realized_pnl=50.0),
            _make_position(status=PositionStatus.CLOSED, realized_pnl=-30.0),
            _make_position(status=PositionStatus.CLOSED, realized_pnl=-20.0),
        ]
        ctx = {"closed_positions": positions}

        tr = read_trackrecord(ctx)
        assert isinstance(tr, TrackRecordSummary)
        assert tr.closed_count == 4
        assert tr.wins == 2
        assert tr.losses == 2
        assert tr.total_pnl == 100.0  # 100 + 50 - 30 - 20
        assert tr.average_pnl == 25.0  # 100 / 4
        assert tr.win_rate == 50.0  # 2/4 * 100

    def test_read_trackrecord_empty(self) -> None:
        tr = read_trackrecord({"closed_positions": []})
        assert tr.closed_count == 0
        assert tr.wins == 0
        assert tr.losses == 0
        assert tr.total_pnl == 0.0
        assert tr.average_pnl == 0.0
        assert tr.win_rate == 0.0

    def test_read_trackrecord_none_ctx(self) -> None:
        tr = read_trackrecord(None)
        assert tr.closed_count == 0
        assert tr.total_pnl == 0.0
        assert tr.win_rate == 0.0

    def test_total_pnl_equals_sum_of_realized_pnl(self) -> None:
        """Equality: display total_pnl == sum(realized_pnl)."""
        positions = [
            _make_position(
                status=PositionStatus.CLOSED, realized_pnl=v
            )
            for v in [10.0, -5.0, 20.0, 7.5]
        ]
        ctx = {"closed_positions": positions}
        tr = read_trackrecord(ctx)
        expected = sum(p.realized_pnl for p in positions)
        assert tr.total_pnl == expected

    def test_average_pnl_equals_total_over_count(self) -> None:
        positions = [
            _make_position(status=PositionStatus.CLOSED, realized_pnl=v)
            for v in [10.0, 20.0, 30.0]
        ]
        ctx = {"closed_positions": positions}
        tr = read_trackrecord(ctx)
        assert tr.average_pnl == tr.total_pnl / tr.closed_count

    def test_zero_pnl_neither_win_nor_loss(self) -> None:
        positions = [
            _make_position(status=PositionStatus.CLOSED, realized_pnl=0.0),
            _make_position(status=PositionStatus.CLOSED, realized_pnl=10.0),
        ]
        ctx = {"closed_positions": positions}
        tr = read_trackrecord(ctx)
        assert tr.wins == 1
        assert tr.losses == 0
        assert tr.closed_count == 2


# ---------- read_latest_signals ----------


class TestReadLatestSignals:
    def test_read_latest_signals_per_symbol(self) -> None:
        s_btc = _make_signal(symbol="BTC")
        s_eth = _make_signal(symbol="ETH")
        repo = _FakeSignalRepo(
            latest_by_symbol={"BTC": s_btc, "ETH": s_eth}
        )
        ctx = {"signal_repository": repo}

        result = read_latest_signals(ctx, ["BTC", "ETH", "BNB"])
        assert len(result) == 2
        assert result[0] is s_btc
        assert result[1] is s_eth

    def test_read_latest_signals_skips_missing(self) -> None:
        s_btc = _make_signal(symbol="BTC")
        repo = _FakeSignalRepo(latest_by_symbol={"BTC": s_btc})
        ctx = {"signal_repository": repo}

        result = read_latest_signals(ctx, ["BTC", "ETH"])
        assert len(result) == 1
        assert result[0] is s_btc

    def test_read_latest_signals_no_repo(self) -> None:
        assert read_latest_signals({}, ["BTC"]) == []
        assert read_latest_signals(None, ["BTC"]) == []

    def test_read_latest_signals_preserves_symbol_order(self) -> None:
        s_eth = _make_signal(symbol="ETH")
        s_btc = _make_signal(symbol="BTC")
        repo = _FakeSignalRepo(
            latest_by_symbol={"ETH": s_eth, "BTC": s_btc}
        )
        ctx = {"signal_repository": repo}

        result = read_latest_signals(ctx, ["BTC", "ETH"])
        assert result[0].symbol == "BTC"
        assert result[1].symbol == "ETH"


# ---------- read_last_signal ----------


class TestReadLastSignal:
    def test_read_last_signal_returns_first_from_history(self) -> None:
        """History sorted desc by created_at → index [0] = newest."""
        s1 = _make_signal(symbol="BTC")
        s2 = _make_signal(symbol="ETH")
        repo = _FakeSignalRepo(history=[s1, s2])
        ctx = {"signal_repository": repo}

        assert read_last_signal(ctx) is s1

    def test_read_last_signal_returns_none_if_empty(self) -> None:
        repo = _FakeSignalRepo(history=[])
        assert read_last_signal({"signal_repository": repo}) is None

    def test_read_last_signal_no_repo(self) -> None:
        assert read_last_signal({}) is None
        assert read_last_signal(None) is None


# ---------- mutation guard ----------


class TestNoMutation:
    def test_use_cases_do_not_mutate_ctx(self) -> None:
        p = _make_position()
        c = _make_position(
            status=PositionStatus.CLOSED, realized_pnl=100.0
        )
        state = _make_state()
        s = _make_signal()
        repo = _FakeSignalRepo(
            latest_by_symbol={"BTC": s},
            history=[s],
        )
        ctx = {
            "positions": [p],
            "closed_positions": [c],
            "portfolio_snapshot": state,
            "signal_repository": repo,
        }

        keys_before = set(ctx.keys())
        positions_before = list(ctx["positions"])
        closed_before = list(ctx["closed_positions"])

        # exercise all read functions
        read_portfolio(ctx)
        read_positions(ctx)
        read_history(ctx)
        read_trackrecord(ctx)
        read_latest_signals(ctx, ["BTC"])
        read_last_signal(ctx)

        assert set(ctx.keys()) == keys_before
        assert ctx["positions"] == positions_before
        assert ctx["closed_positions"] == closed_before
        assert ctx["portfolio_snapshot"] is state
        assert ctx["signal_repository"] is repo


# ---------- bot context price_provider exposure ----------


class TestBotContextPriceProvider:
    """Verify TelegramBot injects the existing (same-instance) price_provider
    into ctx during handle_update and handle_callback.
    """

    def _make_bot(self, price_provider):
        from src.telegram.bot import TelegramBot

        class _FakeRuntime:
            def __init__(self, provider):
                self.price_provider = provider
                self._calls = 0

            def get_context(self):
                self._calls += 1
                return {"positions": [], "closed_positions": []}

        bot = TelegramBot()
        runtime = _FakeRuntime(price_provider)
        bot.set_runtime_provider(runtime)
        return bot, runtime

    def _make_update_for_message(self, text: str = "/help"):
        update = MagicMock()
        update.message = MagicMock()
        update.message.text = text
        update.message.reply_text = AsyncMock()
        update.effective_chat = MagicMock()
        update.effective_chat.id = 12345
        return update

    def _make_update_for_callback(self, data: str = "menu_help"):
        update = MagicMock()
        update.callback_query = MagicMock()
        update.callback_query.data = data
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()
        return update

    async def test_context_exposes_existing_price_provider(
        self, monkeypatch
    ) -> None:
        """ctx['price_provider'] should exist after handle_update."""
        monkeypatch.setattr(
            "src.telegram.bot.TELEGRAM_ALLOWED_USERS", []
        )
        sentinel = object()
        bot, _ = self._make_bot(sentinel)

        update = self._make_update_for_message()
        await bot.handle_update(update, None)

        assert "price_provider" in bot.context
        assert bot.context["price_provider"] is sentinel

    async def test_context_price_provider_is_same_instance(
        self, monkeypatch
    ) -> None:
        """ctx['price_provider'] must be the exact same object, not a copy."""
        monkeypatch.setattr(
            "src.telegram.bot.TELEGRAM_ALLOWED_USERS", []
        )
        sentinel = object()
        bot, runtime = self._make_bot(sentinel)

        update = self._make_update_for_message()
        await bot.handle_update(update, None)

        assert bot.context["price_provider"] is runtime.price_provider
        assert id(bot.context["price_provider"]) == id(runtime.price_provider)

    async def test_callback_context_exposes_same_price_provider(
        self, monkeypatch
    ) -> None:
        """handle_callback refreshes ctx and injects same price_provider."""
        monkeypatch.setattr(
            "src.telegram.bot.TELEGRAM_ALLOWED_USERS", []
        )
        sentinel = object()
        bot, runtime = self._make_bot(sentinel)

        # Pretend a previous command left stale ctx
        bot.context = {"stale": True}

        update = self._make_update_for_callback(data="menu_help")
        await bot.handle_callback(update, None)

        assert bot.context.get("stale") is None  # ctx was refreshed
        assert bot.context["price_provider"] is runtime.price_provider
        assert id(bot.context["price_provider"]) == id(runtime.price_provider)
        assert runtime._calls >= 1  # get_context() was called
