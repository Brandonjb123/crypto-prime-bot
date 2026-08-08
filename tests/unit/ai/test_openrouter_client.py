from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.ai.openrouter_client import OpenRouterClient


@patch("src.ai.openrouter_client.httpx.AsyncClient")
async def test_openrouter_success(mock_client_class):
    mock_client = MagicMock()
    mock_client.__aenter__.return_value = mock_client
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": '{"decision":"BUY","confidence":80,"risk_level":"LOW","reasoning":[]}'}}]
    }
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client_class.return_value = mock_client

    client = OpenRouterClient(api_key="test")
    result = await client.complete("prompt")
    assert result["decision"] == "BUY"


@patch("src.ai.openrouter_client.httpx.AsyncClient")
async def test_openrouter_failure(mock_client_class):
    mock_client = MagicMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.post = AsyncMock(side_effect=Exception("Network error"))
    mock_client_class.return_value = mock_client

    client = OpenRouterClient(api_key="test")
    with pytest.raises(Exception, match="Network error"):
        await client.complete("prompt")