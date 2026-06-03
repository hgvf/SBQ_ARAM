import httpx
from .base import BaseAgentAdapter


class APIAgent(BaseAgentAdapter):
    mode = "api_agent"

    def __init__(self, endpoint: str, method: str = "POST", timeout_seconds: int = 60, input_mapping: dict = None, **kwargs):
        self._endpoint = endpoint
        self._method = method.upper()
        self._timeout = timeout_seconds
        self._input_mapping = input_mapping or {}

    def run(self, context: dict) -> dict:
        payload = {k: context.get(v.lstrip("$."), "") for k, v in self._input_mapping.items()} if self._input_mapping else context
        try:
            if self._method == "POST":
                resp = httpx.post(self._endpoint, json=payload, timeout=self._timeout)
            else:
                resp = httpx.get(self._endpoint, params=payload, timeout=self._timeout)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"error": str(e), "status": "failed"}
