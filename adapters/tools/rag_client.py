import httpx
from loguru import logger


class RAGClient:
    def __init__(self, base_url: str = "http://localhost:8400"):
        self._base_url = base_url.rstrip("/")

    def retrieve_filings(self, ticker: str, query: str = "") -> list[dict]:
        try:
            resp = httpx.post(f"{self._base_url}/retrieve/filings", json={"ticker": ticker, "query": query}, timeout=30)
            resp.raise_for_status()
            return resp.json().get("results", [])
        except Exception as e:
            logger.warning(f"RAG filings retrieval failed: {e}")
            return []

    def retrieve_news(self, ticker: str, query: str = "") -> list[dict]:
        try:
            resp = httpx.post(f"{self._base_url}/retrieve/news", json={"ticker": ticker, "query": query}, timeout=30)
            resp.raise_for_status()
            return resp.json().get("results", [])
        except Exception as e:
            logger.warning(f"RAG news retrieval failed: {e}")
            return []

    def is_available(self) -> bool:
        try:
            httpx.get(f"{self._base_url}/health", timeout=3)
            return True
        except Exception:
            return False
