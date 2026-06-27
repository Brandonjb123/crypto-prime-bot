# services/llm.py
import os
import httpx
from loguru import logger

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = "anthropic/claude-3-haiku"  
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

async def ask_llm(system_prompt: str, prompt: str) -> str:
    logger.info("🚀 ask_llm dipanggil")
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/Brandonjb123/crypto-prime-bot",
        "X-Title": "Crypto Prime Bot",
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

    logger.info(f"📡 Mengirim request ke OpenRouter dengan model {MODEL}...")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(OPENROUTER_URL, json=payload, headers=headers)
            logger.info(f"📬 Response status: {response.status_code}")
            
            # Log response body untuk debug
            logger.info(f"📄 Response body: {response.text[:500]}")
            
            if response.status_code != 200:
                logger.error(f"❌ Full response: {response.text}")
                response.raise_for_status()
            
            data = response.json()
            logger.info(f"📦 Response received")
            return data["choices"][0]["message"]["content"]
    except httpx.TimeoutException:
        logger.error("⏰ Timeout dari OpenRouter")
        raise
    except Exception as e:
        logger.error(f"❌ Error dari OpenRouter: {type(e).__name__}: {e}")
        raise