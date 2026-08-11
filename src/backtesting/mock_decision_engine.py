"""Mock Decision Engine — mengembalikan keputusan yang telah direkam."""

from src.core.models.decision_result import DecisionResult
from src.core.models.market_analysis import AnalysisResult


class MockDecisionEngine:
    def __init__(self, decision: DecisionResult):
        self.decision = decision

    async def decide(self, analysis: AnalysisResult) -> DecisionResult:
        # Mengembalikan keputusan yang sama untuk setiap panggilan (deterministik)
        return self.decision