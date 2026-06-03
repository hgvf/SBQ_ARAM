import uuid
import json
from datetime import datetime, timezone
from pathlib import Path
from loguru import logger
from workflows.base import BaseWorkflowWrapper
from adapters.tools.sbq_quant_client import SBQQuantClient
from adapters.tools.rag_client import RAGClient


SYSTEM_PROMPTS = {
    "data_cot_agent": "You are a financial data analyst. Collect and organize financial data. Return JSON with keys: revenue_trend, earnings_trend, balance_sheet_summary, data_quality.",
    "concept_cot_agent": "You are a financial reasoning agent. Analyze the financial concepts and relationships. Return JSON with keys: business_model, competitive_position, growth_drivers, margin_analysis.",
    "thesis_cot_agent": "You are an investment thesis builder. Construct a clear investment thesis. Return JSON with keys: thesis_summary, catalysts, risks, time_horizon.",
    "valuation_agent": "You are a valuation analyst. Assess the stock's valuation. Return JSON with keys: valuation_view, key_multiples, upside_scenario, downside_scenario.",
    "report_writer": "You are an equity research report writer. Write a comprehensive research report in Markdown format. Include sections: Executive Summary, Business Overview, Financial Analysis, Investment Thesis, Key Risks, Valuation, Conclusion.",
}


class FinRobotWrapper(BaseWorkflowWrapper):
    def __init__(self):
        super().__init__()
        self._sbq = SBQQuantClient()
        self._rag = RAGClient()

    def _call_agent(self, agent_name: str, context: dict, model_alias: str = None) -> dict:
        system = SYSTEM_PROMPTS.get(agent_name, "You are a financial agent.")
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": f"Ticker: {context.get('ticker')}\nCompany: {context.get('company_name', '')}\nDate: {context.get('date')}\nContext: {json.dumps(context, default=str)[:3000]}"},
        ]
        try:
            result = self._llm_router.chat(model_alias or "report_writer", messages)
            content = result.get("content", "")
            if agent_name == "report_writer":
                return {"report_markdown": content}
            from adapters.parsers.json_parser import JSONParser
            return JSONParser().parse(content)
        except Exception as e:
            logger.warning(f"Agent {agent_name} failed: {e}")
            return {"error": str(e), "agent": agent_name}

    def run(self, ticker: str, date: str = None, query: str = "", company_name: str = "", model_alias: str = None, save_trace: bool = True, **kwargs) -> dict:
        trace_id = f"fr_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        started_at = datetime.now(timezone.utc).isoformat()
        date = date or datetime.now(timezone.utc).strftime("%Y-%m-%d")

        logger.info(f"[FinRobot] Starting workflow for {ticker} on {date} | trace={trace_id}")

        # Collect data from external sources
        market_data = {}
        if self._sbq.is_available():
            market_data["fundamentals"] = self._sbq.get_fundamentals(ticker)
            market_data["ohlcv"] = self._sbq.get_ohlcv(ticker, date)

        filings = self._rag.retrieve_filings(ticker, query) if self._rag.is_available() else []
        news = self._rag.retrieve_news(ticker, query) if self._rag.is_available() else []

        context = {
            "ticker": ticker,
            "company_name": company_name or ticker,
            "date": date,
            "query": query,
            "market_data": market_data,
            "filings": filings[:5],
            "news": news[:10],
        }
        agent_steps = []

        for agent in ["data_cot_agent", "concept_cot_agent", "thesis_cot_agent", "valuation_agent"]:
            t0 = datetime.now(timezone.utc)
            output = self._call_agent(agent, context, model_alias)
            latency = int((datetime.now(timezone.utc) - t0).total_seconds() * 1000)
            context[agent] = output
            agent_steps.append({"agent": agent, "override_mode": "passthrough", "model": model_alias or "report_writer", "output": output, "latency_ms": latency, "status": "success"})
            logger.info(f"[FinRobot] {agent} completed")

        # Report writer
        t0 = datetime.now(timezone.utc)
        report_output = self._call_agent("report_writer", context, model_alias)
        latency = int((datetime.now(timezone.utc) - t0).total_seconds() * 1000)
        agent_steps.append({"agent": "report_writer", "override_mode": "passthrough", "model": model_alias or "report_writer", "output": {"report_length": len(report_output.get("report_markdown", ""))}, "latency_ms": latency, "status": "success"})

        ended_at = datetime.now(timezone.utc).isoformat()

        final_output = {
            "workflow": "finrobot",
            "ticker": ticker,
            "company_name": company_name or ticker,
            "date": date,
            "rating_view": context.get("thesis_cot_agent", {}).get("thesis_summary", "neutral"),
            "investment_thesis": context.get("thesis_cot_agent", {}).get("catalysts", []),
            "key_risks": context.get("thesis_cot_agent", {}).get("risks", []),
            "valuation_view": context.get("valuation_agent", {}).get("valuation_view", ""),
            "report_markdown": report_output.get("report_markdown", ""),
            "data_analysis": context.get("data_cot_agent", {}),
            "concept_analysis": context.get("concept_cot_agent", {}),
            "valuation": context.get("valuation_agent", {}),
            "trace_id": trace_id,
        }

        trace = {
            "trace_id": trace_id,
            "workflow": "finrobot",
            "ticker": ticker,
            "date": date,
            "started_at": started_at,
            "ended_at": ended_at,
            "agent_steps": agent_steps,
            "final_output": {k: v for k, v in final_output.items() if k != "report_markdown"},
            "warnings": [],
        }

        if save_trace:
            self._save_trace(trace, final_output)

        return final_output

    def _save_trace(self, trace: dict, full_output: dict):
        path = Path("storage/traces") / f"{trace['trace_id']}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(trace, f, indent=2, default=str)

        report_path = Path("storage/reports") / f"{trace['trace_id']}.md"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, "w") as f:
            f.write(full_output.get("report_markdown", ""))
