# services/llm.py
import os
import httpx
import logging

logger = logging.getLogger(__name__)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = "anthropic/claude-haiku-4-5-20251001"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

async def ask_llm(system_prompt: str, prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL,
        "max_tokens": 800,
        "temperature": 0.3,
        "messages": [
            {"role": "system", "content": system_prompt if system_prompt else "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(OPENROUTER_URL, json=payload, headers=headers, timeout=30.0)
        response.raise_for_status()
        data = response.json()

    return data["choices"][0]["message"]["content"]