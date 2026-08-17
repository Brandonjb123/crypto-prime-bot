"""LLM provider factory."""

from config.settings import settings
from src.ai.groq_client import GroqClient
from src.ai.openrouter_client import OpenRouterClient


def create_llm_client(provider: str | None = None):
    provider = (provider or settings.LLM_PROVIDER).lower()
    if provider == "openrouter":
        return OpenRouterClient(api_key=settings.OPENROUTER_API_KEY)
    if provider == "groq":
        return GroqClient(api_key=settings.GROQ_API_KEY, model=settings.GROQ_MODEL)
    raise ValueError(f"Invalid LLM_PROVIDER: {provider}. Must be 'openrouter' or 'groq'")