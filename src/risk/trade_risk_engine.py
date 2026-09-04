"""Trade Risk Engine — menghitung parameter trading dari ValidatedDecision."""

from datetime import UTC, datetime

from config.constants import (
    ATR_SL_MULTIPLIER,
    DEFAULT_RISK_PERCENT,
)
from src.core.models.trade_plan import TradePlan
from src.core.models.validated_decision import ValidatedDecision
from src.logging.logger import get_logger

logger = get_logger("risk_engine")

MIN_RISK_REWARD = 3.0  # Baseline RR 1:3


class TradeRiskEngine:
    def __init__(
        self,
        risk_percent: float = DEFAULT_RISK_PERCENT,
        atr_sl_multiplier: float = ATR_SL_MULTIPLIER,
    ):
        self.risk_percent = risk_percent
        self.atr_sl_multiplier = atr_sl_multiplier

    def calculate(
        self,
        validated: ValidatedDecision,
        entry_price: float,
        atr: float,
        account_balance: float = 1000.0,
    ) -> TradePlan:
        logger.info("Running risk calculation...")

        if validated.decision == "WAIT":
            logger.info("Decision is WAIT — no position")
            return TradePlan(
                symbol=validated.symbol,
                decision="WAIT",
                entry_price=None,
                position_size=0.0,
                risk_percent=self.risk_percent,
                account_balance=account_balance,
                stop_loss=None,
                take_profit=None,
                take_profit_1=None,
                take_profit_2=None,
                risk_reward_ratio=0.0,
                estimated_loss=0.0,
                estimated_profit=0.0,
                atr_stop_loss=None,
                atr_take_profit=None,
                timestamp=datetime.now(UTC),
            )

        logger.info("Calculating position size...")
        max_risk = account_balance * (self.risk_percent / 100)
        sl_distance = atr * self.atr_sl_multiplier

        if sl_distance <= 0:
            logger.warning("ATR invalid — returning WAIT")
            return TradePlan(
                symbol=validated.symbol,
                decision="WAIT",
                entry_price=None,
                position_size=0.0,
                risk_percent=self.risk_percent,
                account_balance=account_balance,
                stop_loss=None,
                take_profit=None,
                take_profit_1=None,
                take_profit_2=None,
                risk_reward_ratio=0.0,
                estimated_loss=0.0,
                estimated_profit=0.0,
                atr_stop_loss=None,
                atr_take_profit=None,
                timestamp=datetime.now(UTC),
            )

        position_size = max_risk / sl_distance

        # Hitung SL dan TP2 untuk memenuhi RR minimal 1:3
        logger.info("Calculating stop loss...")
        logger.info("Calculating take profit...")

        if validated.decision == "BUY":
            stop_loss = entry_price - sl_distance
            risk = entry_price - stop_loss
            tp2 = entry_price + risk * MIN_RISK_REWARD
            tp1 = entry_price + risk * 1.5  # intermediate target 50% dari TP2
        else:  # SELL
            stop_loss = entry_price + sl_distance
            risk = stop_loss - entry_price
            tp2 = entry_price - risk * MIN_RISK_REWARD
            tp1 = entry_price - risk * 1.5

        risk_reward_ratio = (tp2 - entry_price) / risk if validated.decision == "BUY" else (entry_price - tp2) / risk

        estimated_loss = position_size * sl_distance
        estimated_profit = position_size * (risk * MIN_RISK_REWARD)

        logger.info("TradePlan created")

        return TradePlan(
            symbol=validated.symbol,
            decision=validated.decision,
            entry_price=entry_price,
            position_size=round(position_size, 6),
            risk_percent=self.risk_percent,
            account_balance=account_balance,
            stop_loss=round(stop_loss, 2),
            take_profit=round(tp2, 2),
            take_profit_1=round(tp1, 2),
            take_profit_2=round(tp2, 2),
            risk_reward_ratio=round(risk_reward_ratio, 2),
            estimated_loss=round(estimated_loss, 2),
            estimated_profit=round(estimated_profit, 2),
            atr_stop_loss=round(sl_distance, 2),
            atr_take_profit=round(risk * MIN_RISK_REWARD, 2),
            timestamp=datetime.now(UTC),
        )