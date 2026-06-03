from .base import BaseAgentAdapter
from adapters.llm.router import LLMRouter


class LLMAgent(BaseAgentAdapter):
    mode = "llm_agent"

    def __init__(self, model_alias: str, llm_router: LLMRouter, system_prompt: str = "", **kwargs):
        self._model_alias = model_alias
        self._llm_router = llm_router
        self._system_prompt = system_prompt or "You are a financial analyst. Return structured JSON."

    def run(self, context: dict) -> dict:
        messages = [
            {"role": "system", "content": self._system_prompt},
            {"role": "user", "content": str(context)},
        ]
        return self._llm_router.chat(self._model_alias, messages)
