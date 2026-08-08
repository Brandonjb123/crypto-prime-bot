from datetime import UTC, datetime

from src.ai.prompt_builder import PromptBuilder
from src.core.models.market_analysis import AnalysisResult


def test_prompt_builder():
    builder = PromptBuilder()
    analysis = AnalysisResult(
        symbol="BTC",
        timeframe="4h",
        trend="Bullish",
        momentum="Strong Bullish",
        volatility="Medium",
        volume_strength="High",
        market_structure="Higher High",
        analysis_timestamp=datetime.now(UTC),
    )
    prompt = builder.build(analysis)
    assert "Bullish" in prompt
    assert "Strong Bullish" in prompt
    assert "JSON" in prompt