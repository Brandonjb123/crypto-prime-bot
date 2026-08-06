"""Reversal Risk Model."""

from datetime import UTC, datetime

from config.constants import ATR_MULTIPLIERS, MAX_POSITION_SIZE, RISK_PER_TRADE
from src.core.models.risk import RiskResult
from src.core.models.setup import SetupResult
from src.core.models.snapshot import AnalysisSnapshot
from src.core.models.validation import ValidationResult
from src.core.types.enums import RiskWarning, Side
from src.risk.base_risk_model import BaseRiskModel


class ReversalRiskModel(BaseRiskModel):
    @property
    def name(self) -> str:
        return "reversal"

    def calculate(
        self,
        snapshot: AnalysisSnapshot,
        setup: SetupResult,
        validation: ValidationResult,
    ) -> RiskResult:
        atr = snapshot.technical.atr14 or 100.0
        price = snapshot.price
        direction = setup.direction or Side.LONG
        mult = ATR_MULTIPLIERS["reversal"]
        warnings: list[RiskWarning] = []

        if direction == Side.LONG:
            stop_loss = price - atr * mult["sl"]
            take_profit = price + atr * mult["tp"]
        else:
            stop_loss = price + atr * mult["sl"]
            take_profit = price - atr * mult["tp"]

        stop_distance = abs(price - stop_loss)
        tp_distance = abs(take_profit - price)
        risk_per_unit = stop_distance
        position_size = min(
            (RISK_PER_TRADE * 10000) / risk_per_unit if risk_per_unit > 0 else 0,
            MAX_POSITION_SIZE * 0.7,
        )
        if position_size >= MAX_POSITION_SIZE * 0.7:
            warnings.append(RiskWarning.POSITION_SIZE_CAPPED)

        risk_amount = position_size * risk_per_unit
        expected_profit = position_size * tp_distance
        expected_loss = risk_amount
        rr_ratio = tp_distance / risk_per_unit if risk_per_unit > 0 else 0
        max_loss_pct = (risk_amount / (position_size * price)) * 100 if position_size > 0 else 0

        if rr_ratio < 2.0:
            warnings.append(RiskWarning.RR_TOO_LOW)

        return RiskResult(
            entry_price=price,
            stop_loss=round(stop_loss, 2),
            stop_distance=round(stop_distance, 2),
            take_profit=round(take_profit, 2),
            take_profit_distance=round(tp_distance, 2),
            position_size=round(position_size, 4),
            risk_amount=round(risk_amount, 2),
            expected_profit=round(expected_profit, 2),
            expected_loss=round(expected_loss, 2),
            risk_reward_ratio=round(rr_ratio, 2),
            max_loss_pct=round(max_loss_pct, 2),
            direction=direction,
            risk_model=self.name,
            warnings=warnings,
            timestamp=datetime.now(UTC),
        )