# services/llm.py
import httpx
from config import GROQ_API_KEY

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "llama-3.1-8b-instant"


async def ask_llm(system_prompt: str, user_message: str, model: str = None) -> str:
    if model is None:
        model = DEFAULT_MODEL

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "temperature": 0.3,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            GROQ_API_URL,
            json=payload,
            headers=headers,
            timeout=30.0,
        )
        # DEBUG: cetak status dan body jika bukan 200
        if response.status_code != 200:
            print("ERROR RESPONSE:", response.status_code)
            print(response.text)
        response.raise_for_status()
        data = response.json()

    return data["choices"][0]["message"]["content"] 