from .openai_compatible import OpenAICompatibleProvider


class LlamaCppProvider(OpenAICompatibleProvider):
    provider_name = "llama_cpp"

    def __init__(self, base_url: str = "http://localhost:8080/v1"):
        super().__init__(base_url=base_url, api_key="llama_cpp")
