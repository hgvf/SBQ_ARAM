import httpx
from loguru import logger
from .base import BaseTool


class FinGPTClient:
    def __init__(self, base_url: str = "http://localhost:8200"):
        self._base_url = base_url.rstrip("/")

    def get_sentiment(self, ticker: str, news: list[str], date: str = None) -> dict:
        try:
            resp = httpx.post(f"{self._base_url}/sentiment", json={"ticker": ticker, "news": news, "date": date}, timeout=60)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.warning(f"FinGPT sentiment failed: {e}")
            return {"error": str(e), "available": False}

    def is_available(self) -> bool:
        try:
            httpx.get(f"{self._base_url}/health", timeout=3)
            return True
        except Exception:
            return False
