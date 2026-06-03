from fastapi import APIRouter, HTTPException
from app.schemas.common import WorkflowRequest, WorkflowResponse
from workflows.tradingagents.wrapper import TradingAgentsWrapper
from workflows.finrobot.wrapper import FinRobotWrapper
from loguru import logger

router = APIRouter(prefix="/workflows")

_ta_wrapper = None
_fr_wrapper = None


def get_ta_wrapper():
    global _ta_wrapper
    if _ta_wrapper is None:
        _ta_wrapper = TradingAgentsWrapper()
    return _ta_wrapper


def get_fr_wrapper():
    global _fr_wrapper
    if _fr_wrapper is None:
        _fr_wrapper = FinRobotWrapper()
    return _fr_wrapper


@router.post("/tradingagents/run", response_model=WorkflowResponse)
async def run_tradingagents(request: WorkflowRequest):
    try:
        result = get_ta_wrapper().run(
            ticker=request.ticker,
            date=request.date,
            query=request.query,
            model_alias=request.model_alias,
            save_trace=request.save_trace,
        )
        return WorkflowResponse(workflow="tradingagents", status="success", result=result, trace_id=result.get("trace_id"))
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/finrobot/run", response_model=WorkflowResponse)
async def run_finrobot(request: WorkflowRequest):
    try:
        result = get_fr_wrapper().run(
            ticker=request.ticker,
            date=request.date,
            query=request.query,
            model_alias=request.model_alias,
            save_trace=request.save_trace,
        )
        return WorkflowResponse(workflow="finrobot", status="success", result=result, trace_id=result.get("trace_id"))
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run", response_model=WorkflowResponse)
async def run_auto(request: WorkflowRequest):
    query_lower = (request.query or "").lower()
    report_keywords = ["report", "research", "thesis", "analysis", "fundamental"]
    trade_keywords = ["buy", "sell", "hold", "trade", "decision", "debate"]
    use_fr = any(k in query_lower for k in report_keywords)
    use_ta = any(k in query_lower for k in trade_keywords)
    if use_fr and not use_ta:
        return await run_finrobot(request)
    elif use_ta and not use_fr:
        return await run_tradingagents(request)
    elif use_fr and use_ta:
        fr_result = await run_finrobot(request)
        ta_result = await run_tradingagents(request)
        return WorkflowResponse(
            workflow="auto",
            status="success",
            result={"research": fr_result.result, "trading": ta_result.result},
        )
    else:
        return await run_tradingagents(request)
