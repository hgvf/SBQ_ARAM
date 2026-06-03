from abc import ABC, abstractmethod


class BaseAgentAdapter(ABC):
    mode: str = "base"

    @abstractmethod
    def run(self, context: dict) -> dict:
        ...
