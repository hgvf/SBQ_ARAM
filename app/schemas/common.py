from pydantic import BaseModel
from typing import Any


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.2.0"


class WorkflowRequest(BaseModel):
    ticker: str
    date: str | None = None
    query: str = ""
    override_profile: str = "default"
    save_trace: bool = True
    model_alias: str | None = None


class WorkflowResponse(BaseModel):
    workflow: str
    status: str
    result: dict[str, Any] = {}
    trace_id: str | None = None
    warnings: list[str] = []
