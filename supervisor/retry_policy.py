import time
from loguru import logger


def retry_with_backoff(fn, max_retries: int = 2, base_delay: float = 3.0):
    """Simple retry with exponential backoff."""
    last_exc = None
    for attempt in range(max_retries + 1):
        try:
            return fn()
        except Exception as e:
            last_exc = e
            if attempt < max_retries:
                delay = base_delay * (2 ** attempt)
                logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                time.sleep(delay)
    raise last_exc
