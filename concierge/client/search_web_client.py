import os
import json
from typing import Any
import httpx

from ..models.search_web_input import SearchWebInput


class SearchWebClient:
    async def search_web(input: SearchWebInput, client: Any = None) -> dict:
        """Async search web helper using Serper API.

        This client mirrors the adapters' async style.
        """
        SERPER_API_KEY = os.environ.get("SERPER_API_KEY")
        if not SERPER_API_KEY:
            raise ValueError("SERPER_API_KEY environment variable not set.")

        url = "https://google.serper.dev/search"
        payload = {"q": input.query}
        headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}

        if client is not None:
            resp = await client.post(url, headers=headers, json=payload, timeout=15)
            resp.raise_for_status()
            return resp.json()
        async with httpx.AsyncClient(timeout=15) as c:
            resp = await c.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            return resp.json()
