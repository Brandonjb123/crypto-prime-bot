from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

from src.ai.decision_engine import DecisionEngine
from src.ai.prompt_builder import PromptBuilder
from src.core.models.decision_result import DecisionResult
from src.core.models.market_analysis import AnalysisResult


def _make_analysis():
    return AnalysisResult(
        symbol="BTC",
        timeframe="4h",
        trend="Bullish",
        momentum="Strong Bullish",
        volatility="Medium",
        volume_strength="High",
        market_structure="Higher High",
        analysis_timestamp=datetime.now(UTC),
    )


async def test_decision_engine_success():
    client = MagicMock()
    client.complete = AsyncMock(return_value={
        "decision": "BUY",
        "confidence": 80,
        "risk_level": "LOW",
        "reasoning": ["reason1"],
    })
    builder = PromptBuilder()
    engine = DecisionEngine(client=client, prompt_builder=builder)
    result = await engine.decide(_make_analysis())

    assert isinstance(result, DecisionResult)
    assert result.decision == "BUY"
    assert result.confidence == 80


async def test_decision_engine_fallback():
    client = MagicMock()
    client.complete = AsyncMock(side_effect=Exception("fail"))
    builder = PromptBuilder()
    engine = DecisionEngine(client=client, prompt_builder=builder)
    result = await engine.decide(_make_analysis())

    assert result.decision == "WAIT"
    assert result.confidence == 0
    assert "Invalid AI response" in result.reasoning