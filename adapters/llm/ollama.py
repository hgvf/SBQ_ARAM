from .openai_compatible import OpenAICompatibleProvider


class OllamaProvider(OpenAICompatibleProvider):
    provider_name = "ollama"

    def __init__(self, base_url: str = "http://localhost:11434/v1"):
        super().__init__(base_url=base_url, api_key="ollama")

    def list_models(self) -> list[str]:
        import httpx
        try:
            url = self.base_url.replace("/v1", "") + "/api/tags"
            resp = httpx.get(url, timeout=5)
            data = resp.json()
            return [m["name"] for m in data.get("models", [])]
        except Exception:
            return []
