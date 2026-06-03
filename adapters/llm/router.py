from __future__ import annotations
import yaml
from pathlib import Path
from loguru import logger
from .base import BaseLLMProvider
from .ollama import OllamaProvider
from .llama_cpp import LlamaCppProvider
from .custom_api import CustomAPIProvider


class LLMRouter:
    def __init__(self, model_registry_path: str = "configs/model_registry.yaml", config_path: str = "configs/config.yaml"):
        self._registry: dict = {}
        self._providers: dict[str, BaseLLMProvider] = {}
        self._default_model = "default_reasoner"
        self._load_registry(model_registry_path)
        self._load_config(config_path)

    def _load_registry(self, path: str):
        p = Path(path)
        if p.exists():
            with open(p) as f:
                data = yaml.safe_load(f)
            self._registry = data.get("models", {})

    def _load_config(self, path: str):
        p = Path(path)
        if p.exists():
            with open(p) as f:
                data = yaml.safe_load(f)
            self._default_model = data.get("default_model", "default_reasoner")

    def _get_provider(self, provider_name: str, base_url: str) -> BaseLLMProvider:
        key = f"{provider_name}:{base_url}"
        if key not in self._providers:
            if provider_name == "ollama":
                self._providers[key] = OllamaProvider(base_url=base_url)
            elif provider_name == "llama_cpp":
                self._providers[key] = LlamaCppProvider(base_url=base_url)
            else:
                self._providers[key] = CustomAPIProvider(base_url=base_url)
        return self._providers[key]

    def chat(self, model_alias: str, messages: list[dict], **kwargs) -> dict:
        alias = model_alias or self._default_model
        cfg = self._registry.get(alias)
        if not cfg:
            logger.warning(f"Model alias '{alias}' not found in registry, using default_reasoner")
            cfg = self._registry.get("default_reasoner", {
                "provider": "ollama",
                "base_url": "http://localhost:11434/v1",
                "model": "qwen2.5:7b",
            })
        provider = self._get_provider(cfg["provider"], cfg.get("base_url", "http://localhost:11434/v1"))
        temperature = kwargs.pop("temperature", cfg.get("temperature", 0.2))
        max_tokens = kwargs.pop("max_tokens", cfg.get("max_tokens", 2048))
        return provider.chat(
            model=cfg["model"],
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

    def get_model_config(self, alias: str) -> dict:
        return self._registry.get(alias, {})

    def list_models(self) -> list[str]:
        return list(self._registry.keys())

    def get_default_model(self) -> str:
        return self._default_model

    def set_default_model(self, alias: str):
        if alias in self._registry:
            self._default_model = alias
