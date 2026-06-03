from .base import BaseAgentAdapter


class PassthroughAgent(BaseAgentAdapter):
    mode = "passthrough"

    def __init__(self, upstream_fn, **kwargs):
        self._upstream_fn = upstream_fn

    def run(self, context: dict) -> dict:
        return self._upstream_fn(context)
