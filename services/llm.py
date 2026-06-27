import anthropic
import os
import logging

logger = logging.getLogger(__name__)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
MODEL = "claude-haiku-4-5-20251001"

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

async def ask_llm(system_prompt: str, prompt: str) -> str:
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=800,
            temperature=0.3,
            system=system_prompt if system_prompt else "You are a helpful assistant.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.content[0].text
    except anthropic.APIConnectionError as e:
        logger.error(f"Anthropic connection error: {e}")
        raise
    except anthropic.RateLimitError as e:
        logger.error(f"Anthropic rate limit: {e}")
        raise
    except anthropic.APIStatusError as e:
        logger.error(f"Anthropic API error {e.status_code}: {e.message}")
        raise