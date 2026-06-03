from abc import ABC, abstractmethod


class BaseTool(ABC):
    name: str = "base_tool"
    description: str = ""

    @abstractmethod
    def run(self, **kwargs) -> dict:
        ...
