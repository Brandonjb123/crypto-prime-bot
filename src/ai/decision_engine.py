"""Decision Engine — orchestrator untuk menghasilkan DecisionResult."""

from datetime import UTC, datetime

from loguru import logger

from src.ai.groq_client import GroqRateLimitError
from src.ai.prompt_builder import PromptBuilder
from src.core.models.decision_result import DecisionResult
from src.core.models.market_analysis import AnalysisResult as MarketAnalysis


class DecisionEngine:
    def __init__(self, client, prompt_builder: PromptBuilder):
        self.client = client
        self.prompt_builder = prompt_builder

    async def decide(self, analysis: MarketAnalysis) -> DecisionResult:
        logger.info("Running AI decision...")
        prompt = self.prompt_builder.build(analysis)
        logger.info("Prompt generated")

        logger.info("Sending request to LLM...")
        try:
            response = await self.client.complete(prompt)
            logger.info("AI response received")
            logger.info(f"Decision response={response}")
        except GroqRateLimitError:
            raise
        except Exception as e:
            logger.error(f"LLM failed: {e}")
            return DecisionResult(
                symbol=analysis.symbol,
                decision="WAIT",
                confidence=0,
                risk_level="HIGH",
                reasoning=["Invalid AI response"],
                model="fallback",
                timestamp=datetime.now(UTC),
            )

        logger.info("DecisionResult created")
        return DecisionResult(
            symbol=analysis.symbol,
            decision=response.get("decision", "WAIT"),
            confidence=response.get("confidence", 0),
            risk_level=response.get("risk_level", "HIGH"),
            reasoning=response.get("reasoning", []),
            model="groq",
            timestamp=datetime.now(UTC),
        )