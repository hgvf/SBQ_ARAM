from abc import ABC, abstractmethod
from adapters.llm.router import LLMRouter


class BaseWorkflowWrapper(ABC):
    def __init__(self):
        self._llm_router = LLMRouter()

    @abstractmethod
    def run(self, ticker: str, date: str = None, query: str = "", **kwargs) -> dict:
        ...
