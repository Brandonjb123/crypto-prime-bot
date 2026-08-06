"""Trend Following Risk Model."""

from datetime import UTC, datetime

from config.constants import MAX_POSITION_SIZE, RISK_PER_TRADE
from src.core.models.risk import RiskResult
from src.core.models.setup import SetupResult
from src.core.models.snapshot import AnalysisSnapshot
from src.core.models.validation import ValidationResult
from src.core.types.enums import Side
from src.risk.base_risk_model import BaseRiskModel


class TrendRiskModel(BaseRiskModel):
    @property
    def name(self) -> str:
        return "trend"

    def calculate(
        self,
        snapshot: AnalysisSnapshot,
        setup: SetupResult,
        validation: ValidationResult,
    ) -> RiskResult:
        atr = snapshot.technical.atr14 or 100.0
        price = snapshot.price
        direction = setup.direction or Side.LONG

        # SL/TP berdasarkan ATR
        if direction == Side.LONG:
            stop_loss = price - atr * 2
            take_profit = price + atr * 4
        else:
            stop_loss = price + atr * 2
            take_profit = price - atr * 4

        # Position sizing
        risk_per_unit = abs(price - stop_loss)
        position_size = min(
            (RISK_PER_TRADE * 10000) / risk_per_unit if risk_per_unit > 0 else 0,
            MAX_POSITION_SIZE,
        )
        risk_amount = position_size * risk_per_unit
        rr_ratio = abs(take_profit - price) / risk_per_unit if risk_per_unit > 0 else 0
        max_loss_pct = (risk_amount / (position_size * price)) * 100 if position_size > 0 else 0

        return RiskResult(
            position_size=round(position_size, 4),
            risk_amount=round(risk_amount, 2),
            stop_loss=round(stop_loss, 2),
            take_profit=round(take_profit, 2),
            risk_reward_ratio=round(rr_ratio, 2),
            max_loss_pct=round(max_loss_pct, 2),
            direction=direction,
            risk_model=self.name,
            timestamp=datetime.now(UTC),
        )