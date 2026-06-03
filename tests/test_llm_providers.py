import pytest
from unittest.mock import MagicMock, patch
from adapters.llm.ollama import OllamaProvider
from adapters.llm.router import LLMRouter


def test_ollama_provider_chat_format():
    with patch("adapters.llm.openai_compatible.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"test": true}'
        mock_response.model = "qwen2.5:7b"
        mock_response.usage.model_dump.return_value = {}
        mock_client.chat.completions.create.return_value = mock_response

        provider = OllamaProvider()
        result = provider.chat("qwen2.5:7b", [{"role": "user", "content": "hello"}])
        assert "content" in result


def test_model_registry_loads():
    router = LLMRouter()
    models = router.list_models()
    assert len(models) > 0
    assert "default_reasoner" in models
