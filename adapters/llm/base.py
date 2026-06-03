from abc import ABC, abstractmethod


class BaseLLMProvider(ABC):
    provider_name: str = "base"

    @abstractmethod
    def chat(
        self,
        model: str,
        messages: list[dict],
        temperature: float = 0.2,
        max_tokens: int = 2048,
        response_format: dict | None = None,
        **kwargs,
    ) -> dict:
        ...

    def is_available(self) -> bool:
        return True
