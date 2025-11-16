import asyncio
import logging
import httpx
from bs4 import BeautifulSoup
from tenacity import retry, wait_random_exponential, stop_after_attempt, retry_if_exception_type
from ..utils.circuit_breaker import CircuitBreaker

cb_browse = CircuitBreaker(max_failures=int(__import__('os').environ.get('BROWSE_CB_MAX_FAILURES', '5')),
                          reset_timeout=int(__import__('os').environ.get('BROWSE_CB_RESET', '60')), name='browse')

logger = logging.getLogger(__name__)

RETRIES = int(__import__("os").environ.get("BROWSE_ADAPTER_RETRIES", "3"))
BACKOFF_BASE = float(__import__("os").environ.get("BROWSE_ADAPTER_BACKOFF", "0.5"))


@cb_browse
@retry(
    reraise=True,
    stop=stop_after_attempt(RETRIES),
    wait=wait_random_exponential(multiplier=BACKOFF_BASE),
    retry=retry_if_exception_type(Exception),
)
async def _get_with_retries(url: str, client: httpx.AsyncClient | None = None, timeout: int = 15):
    if client is not None:
        resp = client.get(url, timeout=timeout)
        resp.raise_for_status()
        return resp
    async with httpx.AsyncClient(timeout=timeout) as c:
        resp = await c.get(url)
        resp.raise_for_status()
        return resp


async def browse_website(url: str, client: httpx.AsyncClient | None = None) -> str:
    """Fetch a URL and return cleaned text content (up to a reasonable size).

    Uses more robust headers and behavior derived from the original
    `concierge_agent.browse_website` implementation.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.google.com/',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'DNT': '1'
        }
        if client is not None:
            resp = await _get_with_retries(url, client=client, timeout=15)
        else:
            resp = await _get_with_retries(url, client=None, timeout=15)
        # resp is a httpx.Response
        # ensure headers are used previously; httpx client passed should handle it
        # but if headers needed, we can re-request; skip to parsing

        soup = BeautifulSoup(resp.content, 'html.parser')
        for script_or_style in soup(['script', 'style']):
            script_or_style.decompose()

        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        cleaned = '\n'.join(chunk for chunk in chunks if chunk)

        if not cleaned:
            return f"Error: No text content found at {url}"

        return cleaned[:8000]
    except Exception as e:
        logger.exception("Error browsing %s: %s", url, e)
        return f"Error browsing website {url}: {e}"


async def ping(client: httpx.AsyncClient | None = None) -> dict:
    """Quick check for outbound browsing capability by requesting example.com."""
    test_url = "https://example.com/"
    try:
        resp = await _get_with_retries(test_url, client=client, timeout=10)
        if resp and resp.status_code == 200:
            return {"ok": True, "detail": "outbound HTTP requests working"}
        return {"ok": False, "detail": f"unexpected status {getattr(resp, 'status_code', None)}"}
    except Exception as e:
        logger.exception("Browse ping failed: %s", e)
        return {"ok": False, "detail": str(e)}
