"""Signal Engine — mengubah TradePlan menjadi TradingSignal."""

from datetime import UTC, datetime
from uuid import uuid4

from src.core.models.trade_plan import TradePlan
from src.core.models.trading_signal import TradingSignal
from src.logging.logger import get_logger

logger = get_logger("signal_engine")


class SignalEngine:
    def generate(self, trade_plan: TradePlan) -> TradingSignal:
        logger.info("Generating trading signal...")

        if trade_plan.decision == "WAIT":
            logger.info("Signal status: SKIPPED (WAIT decision)")
            return TradingSignal(
                signal_id=uuid4(),
                symbol=trade_plan.symbol,
                side="WAIT",
                status="SKIPPED",
                entry_price=None,
                stop_loss=None,
                take_profit=None,
                take_profit_1=None,
                take_profit_2=None,
                position_size=0.0,
                risk_percent=trade_plan.risk_percent,
                confidence=0,
                risk_level="MEDIUM",
                reasoning=[],
                created_at=datetime.now(UTC),
            )

        if trade_plan.position_size <= 0:
            logger.info("Signal status: INVALID (position size)")
            return TradingSignal(
                signal_id=uuid4(),
                symbol=trade_plan.symbol,
                side=trade_plan.decision,
                status="INVALID",
                entry_price=trade_plan.entry_price,
                stop_loss=trade_plan.stop_loss,
                take_profit=trade_plan.take_profit,
                take_profit_1=trade_plan.take_profit_1,
                take_profit_2=trade_plan.take_profit_2,
                position_size=0.0,
                risk_percent=trade_plan.risk_percent,
                confidence=0,
                risk_level="MEDIUM",
                reasoning=[],
                created_at=datetime.now(UTC),
            )

        if trade_plan.stop_loss is None or trade_plan.take_profit is None:
            logger.info("Signal status: INVALID (missing SL/TP)")
            return TradingSignal(
                signal_id=uuid4(),
                symbol=trade_plan.symbol,
                side=trade_plan.decision,
                status="INVALID",
                entry_price=trade_plan.entry_price,
                stop_loss=None,
                take_profit=None,
                take_profit_1=None,
                take_profit_2=None,
                position_size=0.0,
                risk_percent=trade_plan.risk_percent,
                confidence=0,
                risk_level="MEDIUM",
                reasoning=[],
                created_at=datetime.now(UTC),
            )

        logger.info("Signal status: ACTIVE")
        return TradingSignal(
            signal_id=uuid4(),
            symbol=trade_plan.symbol,
            side=trade_plan.decision,
            status="ACTIVE",
            entry_price=trade_plan.entry_price,
            stop_loss=trade_plan.stop_loss,
            take_profit=trade_plan.take_profit,
            take_profit_1=trade_plan.take_profit_1,
            take_profit_2=trade_plan.take_profit_2,
            position_size=trade_plan.position_size,
            risk_percent=trade_plan.risk_percent,
            confidence=0,
            risk_level="MEDIUM",
            reasoning=[],
            created_at=datetime.now(UTC),
        )