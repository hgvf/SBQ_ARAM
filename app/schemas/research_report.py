from pydantic import BaseModel
from typing import Any


class ResearchReportSchema(BaseModel):
    workflow: str = "finrobot"
    ticker: str
    date: str
    company_name: str = ""
    rating_view: str = "neutral"
    investment_thesis: list[str] = []
    key_risks: list[str] = []
    valuation_view: str = ""
    report_markdown: str = ""
    trace_id: str | None = None
