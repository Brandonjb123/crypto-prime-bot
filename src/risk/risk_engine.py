"""Risk Engine — orchestrator yang memilih risk model berdasarkan setup type."""

from src.core.models.risk import RiskResult
from src.core.models.setup import SetupResult
from src.core.models.snapshot import AnalysisSnapshot
from src.core.models.validation import ValidationResult
from src.core.types.enums import SetupType
from src.risk.base_risk_model import BaseRiskModel
from src.risk.breakout_risk import BreakoutRiskModel
from src.risk.reversal_risk import ReversalRiskModel
from src.risk.trend_risk import TrendRiskModel


class RiskEngine:
    def __init__(self) -> None:
        self.models: dict[str, BaseRiskModel] = {
            SetupType.TREND_FOLLOWING.value: TrendRiskModel(),
            SetupType.BREAKOUT.value: BreakoutRiskModel(),
            SetupType.REVERSAL.value: ReversalRiskModel(),
        }

    def calculate(
        self,
        snapshot: AnalysisSnapshot,
        setup: SetupResult,
        validation: ValidationResult,
    ) -> RiskResult:
        setup_type = setup.setup_type.value if setup.setup_type else SetupType.TREND_FOLLOWING.value
        model = self.models.get(setup_type, self.models[SetupType.TREND_FOLLOWING.value])
        return model.calculate(snapshot, setup, validation)