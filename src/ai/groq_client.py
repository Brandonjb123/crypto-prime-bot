"""Groq Client — compatible dengan contract DecisionEngine.

Diagnostic logging sementara untuk menangkap HTTP error body.
TIDAK menyimpan/menampilkan API key atau Authorization header.
"""

import asyncio
import json

import httpx
from loguru import logger

GROQ_CHAT_COMPLETIONS_URL = "https://api.groq.com/openai/v1/chat/completions"
TIMEOUT = 30.0
MAX_5XX_ATTEMPTS = 3
MAX_429_ATTEMPTS = 2
RETRY_DELAY_SECONDS = 1.0


class GroqRateLimitError(Exception):
    """Raised saat rate limit TPD/TPM tercapai."""


class GroqClient:
    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile"):
        if not api_key:
            raise ValueError("GROQ_API_KEY is required")
        self.api_key = api_key
        self.model = model

    async def complete(self, prompt: str) -> dict:
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        return await self._request_with_retry(headers, payload)

    async def _request_with_retry(self, headers: dict, payload: dict) -> dict:
        for attempt in range(1, MAX_5XX_ATTEMPTS + 1):
            try:
                async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                    response = await client.post(
                        GROQ_CHAT_COMPLETIONS_URL,
                        json=payload,
                        headers=headers,
                    )

                status = response.status_code

                if status in (400, 401, 403):
                    self._log_http_error(response, status)
                    raise ValueError(f"Groq API error: HTTP {status}")

                if status == 429:
                    if attempt >= MAX_429_ATTEMPTS:
                        self._log_http_error(response, status)
                        raise GroqRateLimitError("Groq rate limit retry exhausted")
                    await asyncio.sleep(RETRY_DELAY_SECONDS * attempt)
                    continue

                if 500 <= status < 600:
                    if attempt >= MAX_5XX_ATTEMPTS:
                        self._log_http_error(response, status)
                        raise ValueError("Groq server error retry exhausted")
                    await asyncio.sleep(RETRY_DELAY_SECONDS * attempt)
                    continue

                if status != 200:
                    self._log_http_error(response, status)
                    raise ValueError(f"Groq API error: HTTP {status}")

                data = response.json()
                content = data["choices"][0]["message"]["content"]
                return json.loads(content)

            except GroqRateLimitError:
                raise
            except json.JSONDecodeError:
                raise
            except ValueError:
                raise
            except (httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError) as e:
                if attempt >= MAX_5XX_ATTEMPTS:
                    logger.error(f"Groq network/timeout retry exhausted: {type(e).__name__}")
                    raise
                await asyncio.sleep(RETRY_DELAY_SECONDS * attempt)
            except Exception as e:
                if attempt >= MAX_5XX_ATTEMPTS:
                    logger.error(f"Groq unexpected error: {type(e).__name__}: {e}")
                    raise
                await asyncio.sleep(RETRY_DELAY_SECONDS * attempt)

        raise RuntimeError("Groq request failed")

    def _log_http_error(self, response: httpx.Response, status: int) -> None:
        """Log error response body tanpa mengekspos kredensial."""
        error_code = None
        error_message = None
        body_preview = ""

        try:
            body = response.json()
            if isinstance(body, dict):
                err = body.get("error") or {}
                if isinstance(err, dict):
                    error_code = err.get("code")
                    error_message = err.get("message")
            body_preview = response.text[:500]
        except Exception:
            body_preview = response.text[:500]

        logger.error(
            "Groq API error | "
            f"status={status} "
            f"model={self.model} "
            f"endpoint={GROQ_CHAT_COMPLETIONS_URL} "
            f"error_code={error_code} "
            f"error_message={error_message} "
            f"body_preview={body_preview}"
        )

        if error_message:
            raise ValueError(f"Groq API error: {error_message} (HTTP {status})")
        raise ValueError(f"Groq API error: HTTP {status} — {body_preview}")