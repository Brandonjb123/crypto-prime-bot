"""Decision Engine — orchestrator untuk menghasilkan DecisionResult."""

import json
from datetime import UTC, datetime
from json import JSONDecodeError

from loguru import logger

from src.ai.groq_client import AIDecisionUnavailableError
from src.ai.prompt_builder import PromptBuilder
from src.core.models.decision_result import DecisionResult


class DecisionEngine:
    def __init__(self, client, prompt_builder: PromptBuilder):
        self.client = client
        self.prompt_builder = prompt_builder

    async def decide(self, analysis) -> DecisionResult:
        """Jalankan AI decision. Raise AIDecisionUnavailableError jika LLM gagal."""
        prompt = self.prompt_builder.build(analysis)
        logger.info("Prompt generated")

        logger.info("Sending request to LLM...")
        try:
            raw = await self.client.complete(prompt)
        except Exception as e:
            raise AIDecisionUnavailableError(str(e)) from e

        logger.info("AI response received")

        # Tangani response dalam bentuk dict atau string JSON
        if isinstance(raw, dict):
            data = raw
        elif isinstance(raw, str):
            try:
                data = json.loads(raw)
            except JSONDecodeError:
                raise AIDecisionUnavailableError("Invalid JSON from LLM") from None
        else:
            raise AIDecisionUnavailableError("Unexpected LLM response type") from None

        decision = data.get("decision", "WAIT").upper()
        confidence = int(data.get("confidence", 0))
        risk_level = data.get("risk_level", "MEDIUM")
        reasoning = data.get("reasoning", [])

        result = DecisionResult(
            symbol=analysis.symbol,
            decision=decision,
            confidence=confidence,
            risk_level=risk_level,
            reasoning=reasoning,
            model=self._get_model_name(),
            timestamp=datetime.now(UTC),
        )
        logger.info("DecisionResult created")
        return result

    def _get_model_name(self) -> str:
        model_attr = getattr(self.client, "model", None)
        return model_attr if isinstance(model_attr, str) else "unknown"