import os
import json
import asyncio
import logging
from typing import Any
import httpx
from tenacity import retry, wait_random_exponential, stop_after_attempt, retry_if_exception_type, RetryError

logger = logging.getLogger(__name__)

SERPER_API_KEY = os.environ.get("SERPER_API_KEY")

RETRIES = int(os.environ.get("SEARCH_ADAPTER_RETRIES", "3"))
BACKOFF_BASE = float(os.environ.get("SEARCH_ADAPTER_BACKOFF", "0.5"))


from ..utils.circuit_breaker import CircuitBreaker

cb_search = CircuitBreaker(max_failures=int(__import__('os').environ.get('SEARCH_CB_MAX_FAILURES', '5')), 
                           reset_timeout=int(__import__('os').environ.get('SEARCH_CB_RESET', '60')), name='search')


@cb_search
@retry(
    reraise=True,
    stop=stop_after_attempt(RETRIES),
    wait=wait_random_exponential(multiplier=BACKOFF_BASE),
    retry=retry_if_exception_type(httpx.HTTPError),
)
async def _post_with_retries(url: str, headers: dict, payload: dict, client: Any = None, timeout: int = 15):
    if client is not None:
        resp = client.post(url, headers=headers, json=payload, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    async with httpx.AsyncClient(timeout=timeout) as c:
        resp = await c.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        return resp.json()


async def search_web(query: str, client: Any = None) -> dict[str, Any]:
    """Perform a web search using Serper and return the parsed JSON response.

    This mirrors the behavior of the original `concierge_agent.search_web` tool,
    returning the provider JSON where possible or an error dict with `text` for
    human-friendly output.
    """
    if not SERPER_API_KEY:
        msg = "Error: SERPER_API_KEY is not set. Cannot perform web search."
        logger.error(msg)
        return {"error": msg, "text": msg}

    url = "https://google.serper.dev/search"
    payload = {"q": query}
    headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}

    try:
        results = await _post_with_retries(url, headers, payload, client=client, timeout=15)

        # Provide a human-readable `text` field similar to the original script
        if isinstance(results, dict) and results.get("organic"):
            output = "Search Results:\n"
            for item in results["organic"][:5]:
                output += f"- Title: {item.get('title', 'N/A')}\n"
                output += f"  Link: {item.get('link', 'N/A')}\n"
                output += f"  Snippet: {item.get('snippet', 'N/A')}\n\n"
            results.setdefault("text", output)
        else:
            if isinstance(results, dict):
                results.setdefault("text", "No good search results found.")

        return results
    except httpx.HTTPError as e:
        msg = f"Error during web search: {e}"
        logger.exception(msg)
        return {"error": str(e), "text": msg}
    except Exception as e:
        msg = f"Error during web search: {e}"
        logger.exception(msg)
        return {"error": str(e), "text": msg}


async def ping(client: Any = None) -> dict:
    """Quick health check for the search provider.

    Returns a dict: {"ok": bool, "detail": str}
    """
    if not SERPER_API_KEY:
        return {"ok": False, "detail": "SERPER_API_KEY not set"}
    try:
        resp = await search_web("status check", client=client)
        if isinstance(resp, dict) and resp.get("error"):
            return {"ok": False, "detail": resp.get("text") or resp.get("error")}
        return {"ok": True, "detail": "search provider reachable"}
    except Exception as e:
        logger.exception("Search ping failed: %s", e)
        return {"ok": False, "detail": str(e)}
