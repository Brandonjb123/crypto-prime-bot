"""Unit tests untuk provider factory."""

import pytest

from src.ai.groq_client import GroqClient
from src.ai.openrouter_client import OpenRouterClient
from src.ai.provider_factory import create_llm_client


def test_provider_openrouter(monkeypatch):
    monkeypatch.setattr("src.ai.provider_factory.settings.OPENROUTER_API_KEY", "test-key")
    client = create_llm_client("openrouter")
    assert isinstance(client, OpenRouterClient)


def test_provider_groq(monkeypatch):
    monkeypatch.setattr("src.ai.provider_factory.settings.GROQ_API_KEY", "test-key")
    monkeypatch.setattr("src.ai.provider_factory.settings.GROQ_MODEL", "test-model")
    client = create_llm_client("groq")
    assert isinstance(client, GroqClient)
    assert client.model == "test-model"


def test_provider_invalid():
    with pytest.raises(ValueError):
        create_llm_client("invalid")