import httpx
from loguru import logger


class NewsClient:
    def __init__(self, base_url: str = None):
        self._base_url = base_url

    def get_news(self, ticker: str, limit: int = 10) -> list[dict]:
        # Placeholder: returns empty list when no news API configured
        return []
