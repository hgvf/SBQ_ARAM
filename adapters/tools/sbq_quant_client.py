import httpx
from loguru import logger
from .base import BaseTool


class SBQQuantClient:
    def __init__(self, base_url: str = "http://localhost:8001"):
        self._base_url = base_url.rstrip("/")

    def _get(self, path: str, params: dict = None) -> dict:
        try:
            resp = httpx.get(f"{self._base_url}{path}", params=params or {}, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.warning(f"SBQ-Quant {path} failed: {e}")
            return {"error": str(e), "available": False}

    def get_ohlcv(self, ticker: str, date: str = None) -> dict:
        return self._get("/ohlcv", {"ticker": ticker, "date": date})

    def get_indicators(self, ticker: str, date: str = None) -> dict:
        return self._get("/indicators", {"ticker": ticker, "date": date})

    def get_risk_snapshot(self, ticker: str) -> dict:
        return self._get("/risk/snapshot", {"ticker": ticker})

    def get_fundamentals(self, ticker: str) -> dict:
        return self._get("/fundamentals", {"ticker": ticker})

    def get_signals(self, ticker: str, date: str = None) -> dict:
        return self._get("/signals", {"ticker": ticker, "date": date})

    def is_available(self) -> bool:
        try:
            httpx.get(f"{self._base_url}/health", timeout=3)
            return True
        except Exception:
            return False
