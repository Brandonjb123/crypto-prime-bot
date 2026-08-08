"""OpenRouter Client — kirim prompt ke Claude Haiku via OpenRouter."""

import asyncio
import json

import httpx
from loguru import logger

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "anthropic/claude-3-haiku"
MAX_RETRIES = 3
RETRY_DELAY = 1.0
TIMEOUT = 30.0


class OpenRouterClient:
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def complete(self, prompt: str) -> dict:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
        }

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                    response = await client.post(OPENROUTER_URL, json=payload, headers=headers)
                    response.raise_for_status()
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]
                    return json.loads(content)
            except Exception as e:
                logger.warning(f"OpenRouter attempt {attempt}/{MAX_RETRIES} failed: {e}")
                if attempt == MAX_RETRIES:
                    raise
                await asyncio.sleep(RETRY_DELAY * attempt)