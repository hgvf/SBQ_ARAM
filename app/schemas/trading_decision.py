from pydantic import BaseModel
from typing import Any


class RiskAssessment(BaseModel):
    risk_level: str = "medium"
    position_limit: float = 0.05
    must_reduce_if: list[str] = []


class RecommendedAction(BaseModel):
    action: str = "hold"
    max_weight: float = 0.05
    requires_quant_validation: bool = True


class TradingDecisionSchema(BaseModel):
    workflow: str = "tradingagents"
    ticker: str
    date: str
    decision: str = "hold"
    confidence: float = 0.5
    time_horizon: str = "2w"
    bull_case: list[str] = []
    bear_case: list[str] = []
    risk_assessment: dict[str, Any] = {}
    recommended_action: dict[str, Any] = {}
    trace_id: str | None = None
