import httpx
from openai import OpenAI
from .base import BaseLLMProvider


class OpenAICompatibleProvider(BaseLLMProvider):
    provider_name = "openai_compatible"

    def __init__(self, base_url: str, api_key: str = "ollama"):
        self.base_url = base_url
        self.api_key = api_key
        self._client = OpenAI(base_url=base_url, api_key=api_key)

    def chat(self, model, messages, temperature=0.2, max_tokens=2048, response_format=None, **kwargs):
        kwargs_extra = {}
        if response_format:
            kwargs_extra["response_format"] = response_format
        resp = self._client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs_extra,
        )
        return {
            "content": resp.choices[0].message.content,
            "model": resp.model,
            "usage": resp.usage.model_dump() if resp.usage else {},
        }

    def is_available(self) -> bool:
        try:
            httpx.get(self.base_url.rstrip("/v1").rstrip("/") + "/api/tags", timeout=3)
            return True
        except Exception:
            return False
