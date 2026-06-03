from .openai_compatible import OpenAICompatibleProvider


class CustomAPIProvider(OpenAICompatibleProvider):
    provider_name = "custom_api"

    def __init__(self, base_url: str, api_key: str = "custom"):
        super().__init__(base_url=base_url, api_key=api_key)
