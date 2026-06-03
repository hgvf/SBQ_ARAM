import uuid
import json
from datetime import datetime, timezone
from pathlib import Path
from loguru import logger
from workflows.base import BaseWorkflowWrapper
from adapters.llm.router import LLMRouter
from adapters.tools.sbq_quant_client import SBQQuantClient


SYSTEM_PROMPTS = {
    "fundamental_analyst": "You are a fundamental analyst. Analyze the company's financial health and business model. Return JSON with keys: view, key_metrics, confidence.",
    "sentiment_analyst": "You are a market sentiment analyst. Analyze news and market sentiment. Return JSON with keys: sentiment, score, confidence, main_events.",
    "technical_analyst": "You are a technical analyst. Analyze price action and technical indicators. Return JSON with keys: trend, momentum, support, resistance, confidence.",
    "bull_researcher": "You are a bullish researcher. Present the strongest bullish arguments. Return JSON with keys: thesis, catalysts, confidence.",
    "bear_researcher": "You are a bearish researcher. Present the strongest bearish arguments. Return JSON with keys: thesis, risks, confidence.",
    "trader": "You are a trader synthesizing analyst views. Decide on an action. Return JSON with keys: decision (buy/sell/hold/increase_weight/decrease_weight), rationale, confidence.",
    "risk_manager": "You are a risk manager. Review the proposed trade. Return JSON with keys: approved, risk_level, position_limit, conditions.",
}


class TradingAgentsWrapper(BaseWorkflowWrapper):
    def __init__(self):
        super().__init__()
        self._sbq = SBQQuantClient()

    def _call_agent(self, agent_name: str, context: dict, model_alias: str = None) -> dict:
        system = SYSTEM_PROMPTS.get(agent_name, "You are a financial agent.")
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": f"Ticker: {context.get('ticker')}\nDate: {context.get('date')}\nContext: {json.dumps(context, default=str)[:3000]}"},
        ]
        try:
            result = self._llm_router.chat(model_alias or "default_reasoner", messages)
            from adapters.parsers.json_parser import JSONParser
            return JSONParser().parse(result.get("content", "{}"))
        except Exception as e:
            logger.warning(f"Agent {agent_name} failed: {e}")
            return {"error": str(e), "agent": agent_name}

    def run(self, ticker: str, date: str = None, query: str = "", model_alias: str = None, save_trace: bool = True, **kwargs) -> dict:
        trace_id = f"ta_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        started_at = datetime.now(timezone.utc).isoformat()
        date = date or datetime.now(timezone.utc).strftime("%Y-%m-%d")

        logger.info(f"[TradingAgents] Starting workflow for {ticker} on {date} | trace={trace_id}")

        # Step 1: Collect market data
        market_data = {}
        if self._sbq.is_available():
            market_data["ohlcv"] = self._sbq.get_ohlcv(ticker, date)
            market_data["indicators"] = self._sbq.get_indicators(ticker, date)
            market_data["signals"] = self._sbq.get_signals(ticker, date)

        context = {"ticker": ticker, "date": date, "query": query, "market_data": market_data}
        agent_steps = []

        # Step 2: Run analyst agents
        for agent in ["fundamental_analyst", "sentiment_analyst", "technical_analyst"]:
            t0 = datetime.now(timezone.utc)
            output = self._call_agent(agent, context, model_alias)
            latency = int((datetime.now(timezone.utc) - t0).total_seconds() * 1000)
            context[agent] = output
            agent_steps.append({"agent": agent, "override_mode": "passthrough", "model": model_alias or "default_reasoner", "output": output, "latency_ms": latency, "status": "success"})
            logger.info(f"[TradingAgents] {agent} completed")

        # Step 3: Bull/Bear debate
        for agent in ["bull_researcher", "bear_researcher"]:
            t0 = datetime.now(timezone.utc)
            output = self._call_agent(agent, context, model_alias)
            latency = int((datetime.now(timezone.utc) - t0).total_seconds() * 1000)
            context[agent] = output
            agent_steps.append({"agent": agent, "override_mode": "passthrough", "model": model_alias or "default_reasoner", "output": output, "latency_ms": latency, "status": "success"})
            logger.info(f"[TradingAgents] {agent} completed")

        # Step 4: Trader synthesis
        t0 = datetime.now(timezone.utc)
        trader_output = self._call_agent("trader", context, model_alias)
        latency = int((datetime.now(timezone.utc) - t0).total_seconds() * 1000)
        context["trader"] = trader_output
        agent_steps.append({"agent": "trader", "override_mode": "passthrough", "model": model_alias or "default_reasoner", "output": trader_output, "latency_ms": latency, "status": "success"})

        # Step 5: Risk manager review
        t0 = datetime.now(timezone.utc)
        risk_output = self._call_agent("risk_manager", context, model_alias)
        latency = int((datetime.now(timezone.utc) - t0).total_seconds() * 1000)
        agent_steps.append({"agent": "risk_manager", "override_mode": "passthrough", "model": model_alias or "default_reasoner", "output": risk_output, "latency_ms": latency, "status": "success"})

        ended_at = datetime.now(timezone.utc).isoformat()

        final_output = {
            "workflow": "tradingagents",
            "ticker": ticker,
            "date": date,
            "decision": trader_output.get("decision", "hold"),
            "confidence": trader_output.get("confidence", 0.5),
            "bull_case": context.get("bull_researcher", {}).get("thesis", []),
            "bear_case": context.get("bear_researcher", {}).get("thesis", []),
            "sentiment": context.get("sentiment_analyst", {}),
            "technical": context.get("technical_analyst", {}),
            "fundamental": context.get("fundamental_analyst", {}),
            "risk_assessment": risk_output,
            "trace_id": trace_id,
        }

        trace = {
            "trace_id": trace_id,
            "workflow": "tradingagents",
            "ticker": ticker,
            "date": date,
            "started_at": started_at,
            "ended_at": ended_at,
            "agent_steps": agent_steps,
            "final_output": final_output,
            "warnings": [],
        }

        if save_trace:
            self._save_trace(trace)

        return final_output

    def _save_trace(self, trace: dict):
        path = Path("storage/traces") / f"{trace['trace_id']}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(trace, f, indent=2, default=str)

        decision_path = Path("storage/decisions") / f"{trace['trace_id']}.json"
        decision_path.parent.mkdir(parents=True, exist_ok=True)
        with open(decision_path, "w") as f:
            json.dump(trace["final_output"], f, indent=2, default=str)
