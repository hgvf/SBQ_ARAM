from pydantic import BaseModel
from typing import Any


class AgentStep(BaseModel):
    agent: str
    override_mode: str = "passthrough"
    model: str = ""
    input_hash: str = ""
    output: dict[str, Any] = {}
    latency_ms: int = 0
    status: str = "success"


class TraceSchema(BaseModel):
    trace_id: str
    workflow: str
    ticker: str
    date: str
    started_at: str
    ended_at: str
    agent_steps: list[AgentStep] = []
    final_output: dict[str, Any] = {}
    warnings: list[str] = []
