"""Unit tests untuk GroqClient."""

import json

import httpx
import pytest
import respx

from src.ai.groq_client import GroqClient


@pytest.fixture
def client():
    return GroqClient(api_key="test-groq-key", model="test-model")


class TestGroqClient:
    @respx.mock
    async def test_successful_response(self, client):
        content = json.dumps({"decision": "BUY", "confidence": 88, "risk_level": "MEDIUM", "reasoning": ["reason"]})
        route = respx.post("https://api.groq.com/openai/v1/chat/completions").mock(
            return_value=httpx.Response(200, json={"choices": [{"message": {"content": content}}]})
        )

        result = await client.complete("test prompt")

        assert result["decision"] == "BUY"
        assert result["confidence"] == 88
        assert route.called
        request = route.calls.last.request
        assert request.url == "https://api.groq.com/openai/v1/chat/completions"
        assert request.headers["Authorization"] == "Bearer test-groq-key"
        body = json.loads(request.content)
        assert body["model"] == "test-model"

    @respx.mock
    async def test_correct_model(self, client):
        content = json.dumps({"decision": "WAIT", "confidence": 0, "risk_level": "HIGH", "reasoning": []})
        route = respx.post("https://api.groq.com/openai/v1/chat/completions").mock(
            return_value=httpx.Response(200, json={"choices": [{"message": {"content": content}}]})
        )
        await client.complete("test")
        assert json.loads(route.calls.last.request.content)["model"] == "test-model"

    @respx.mock
    async def test_correct_endpoint(self, client):
        content = json.dumps({"decision": "WAIT", "confidence": 0, "risk_level": "HIGH", "reasoning": []})
        route = respx.post("https://api.groq.com/openai/v1/chat/completions").mock(
            return_value=httpx.Response(200, json={"choices": [{"message": {"content": content}}]})
        )
        await client.complete("test")
        assert route.calls.last.request.url == "https://api.groq.com/openai/v1/chat/completions"

    @respx.mock
    async def test_correct_authorization_header(self, client):
        content = json.dumps({"decision": "WAIT", "confidence": 0, "risk_level": "HIGH", "reasoning": []})
        route = respx.post("https://api.groq.com/openai/v1/chat/completions").mock(
            return_value=httpx.Response(200, json={"choices": [{"message": {"content": content}}]})
        )
        await client.complete("test")
        assert route.calls.last.request.headers["Authorization"] == "Bearer test-groq-key"

    @respx.mock
    async def test_json_parsing(self, client):
        content = json.dumps({"decision": "SELL", "confidence": 50, "risk_level": "LOW", "reasoning": []})
        respx.post("https://api.groq.com/openai/v1/chat/completions").mock(
            return_value=httpx.Response(200, json={"choices": [{"message": {"content": content}}]})
        )
        result = await client.complete("test")
        assert result == {"decision": "SELL", "confidence": 50, "risk_level": "LOW", "reasoning": []}

    @respx.mock
    async def test_malformed_json(self, client):
        respx.post("https://api.groq.com/openai/v1/chat/completions").mock(
            return_value=httpx.Response(200, json={"choices": [{"message": {"content": "not-json"}}]})
        )
        with pytest.raises(json.JSONDecodeError):
            await client.complete("test")

    @respx.mock
    async def test_http_401_no_retry(self, client):
        route = respx.post("https://api.groq.com/openai/v1/chat/completions").mock(
            return_value=httpx.Response(401, json={"error": "unauthorized"})
        )
        with pytest.raises(ValueError):
            await client.complete("test")
        assert route.call_count == 1

    @respx.mock
    async def test_http_403_no_retry(self, client):
        route = respx.post("https://api.groq.com/openai/v1/chat/completions").mock(
            return_value=httpx.Response(403, json={"error": "forbidden"})
        )
        with pytest.raises(ValueError):
            await client.complete("test")
        assert route.call_count == 1

    @respx.mock
    async def test_http_429_bounded_retry(self, client):
        route = respx.post("https://api.groq.com/openai/v1/chat/completions").mock(
            side_effect=[
                httpx.Response(429, json={"error": "rate limit"}),
                httpx.Response(429, json={"error": "rate limit"}),
            ]
        )
        with pytest.raises(ValueError):
            await client.complete("test")
        assert route.call_count == 2

    @respx.mock
    async def test_http_5xx_bounded_retry(self, client):
        route = respx.post("https://api.groq.com/openai/v1/chat/completions").mock(
            side_effect=[
                httpx.Response(500, json={"error": "server"}),
                httpx.Response(500, json={"error": "server"}),
                httpx.Response(500, json={"error": "server"}),
            ]
        )
        with pytest.raises(ValueError):
            await client.complete("test")
        assert route.call_count == 3

    @respx.mock
    async def test_timeout_bounded_retry(self, client):
        route = respx.post("https://api.groq.com/openai/v1/chat/completions").mock(
            side_effect=httpx.TimeoutException("timeout")
        )
        with pytest.raises(httpx.TimeoutException):
            await client.complete("test")
        assert route.call_count == 3

    def test_missing_api_key(self):
        with pytest.raises(ValueError):
            GroqClient(api_key="")