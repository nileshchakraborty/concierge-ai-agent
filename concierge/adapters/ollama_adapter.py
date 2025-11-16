import os
import asyncio
import base64
import logging
import httpx
from typing import Any, Iterable
from tenacity import retry, wait_random_exponential, stop_after_attempt, retry_if_exception_type
from ..utils.circuit_breaker import CircuitBreaker

cb_ollama = CircuitBreaker(max_failures=int(__import__('os').environ.get('OLLAMA_CB_MAX_FAILURES', '3')),
                         reset_timeout=int(__import__('os').environ.get('OLLAMA_CB_RESET', '30')), name='ollama')

logger = logging.getLogger(__name__)

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "gemma3:4b")

RETRIES = int(os.environ.get("OLLAMA_ADAPTER_RETRIES", "3"))
BACKOFF_BASE = float(os.environ.get("OLLAMA_ADAPTER_BACKOFF", "0.5"))


def encode_image(image_path: str) -> str:
    """Encode an image file to a base64 string suitable for embedding in an Ollama payload."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


async def call_gemma(prompt: str, *, max_tokens: int = 1024, client: httpx.AsyncClient | None = None,
                     output_format: str = "text", images: Iterable[str] | None = None) -> dict[str, Any]:
    """Call local Ollama and return a dict with `text` on success or `error`.

    Parameters:
    - prompt: the prompt text
    - max_tokens: token limit for the model
    - client: optional `httpx.AsyncClient` to reuse
    - output_format: 'text' or 'json' (affects payload.format)
    - images: optional iterable of local image file paths to include
    """
    url = f"{OLLAMA_HOST}/api/generate"
    payload: dict[str, Any] = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "max_tokens": max_tokens,
        "stream": False,
    }

    if output_format in ("json", "jsonl"):
        payload["format"] = output_format

    if images:
        encoded = [encode_image(p) for p in images]
        if encoded:
            payload["images"] = encoded

    # perform request with simple retry/backoff
    @cb_ollama
    @retry(
        reraise=True,
        stop=stop_after_attempt(RETRIES),
        wait=wait_random_exponential(multiplier=BACKOFF_BASE),
        retry=retry_if_exception_type(httpx.HTTPError),
    )
    async def _post():
        if client is not None:
            resp = client.post(url, json=payload, timeout=60)
        else:
            async with httpx.AsyncClient(timeout=60) as c:
                resp = await c.post(url, json=payload)
        resp.raise_for_status()
        return resp.json()

    try:
        data = await _post()
    except Exception as last_exc:
        logger.exception("Ollama adapter all attempts failed: %s", last_exc)
        return {"error": str(last_exc)}

    # Ollama responses vary; try to extract a useful field
    if isinstance(data, dict):
        text = data.get("response") or data.get("text") or data.get("output")
        if isinstance(text, (dict, list)):
            text = str(text)
        if text:
            return {"text": text}
        return {"text": str(data)}

    return {"text": str(data)}


async def ping(client: httpx.AsyncClient | None = None) -> dict:
    """Health check for local Ollama server. Attempts a lightweight generate call.

    Returns {"ok": bool, "detail": str}
    """
    test_prompt = "Ping"
    try:
        resp = await call_gemma(test_prompt, max_tokens=1, client=client)
        if isinstance(resp, dict) and resp.get("error"):
            return {"ok": False, "detail": resp.get("error")}
        return {"ok": True, "detail": "ollama reachable"}
    except Exception as e:
        logger.exception("Ollama ping failed: %s", e)
        return {"ok": False, "detail": str(e)}
