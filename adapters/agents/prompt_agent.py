import yaml
from pathlib import Path
from .base import BaseAgentAdapter
from adapters.llm.router import LLMRouter


class PromptAgent(BaseAgentAdapter):
    mode = "prompt_override"

    def __init__(self, prompt_path: str, model_alias: str, llm_router: LLMRouter, **kwargs):
        self._prompt_cfg = self._load_prompt(prompt_path)
        self._model_alias = model_alias
        self._llm_router = llm_router

    def _load_prompt(self, path: str) -> dict:
        p = Path(path)
        if p.exists():
            with open(p) as f:
                return yaml.safe_load(f)
        return {"system": "You are a financial analyst.", "input_variables": []}

    def run(self, context: dict) -> dict:
        system_prompt = self._prompt_cfg.get("system", "")
        user_content = str(context)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]
        return self._llm_router.chat(self._model_alias, messages)
