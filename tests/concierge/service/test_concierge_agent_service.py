import json
import pytest

from concierge.service.di import get_ai_agent_service, get_concierge_service
from concierge.service.impl.concierge_agent_service import ConciergeAgentService


@pytest.mark.asyncio
async def test_concierge_flow(monkeypatch):
    from concierge.adapters import search_adapter, browse_adapter, ollama_adapter, email_adapter

    async def async_search(q, **k):
        return {"text": "results", "organic": [{"link": "http://a"}]}

    async def async_browse(u, **k):
        return "page a content"

    async def fake_model(prompt, **k):
        return {"text": "SUMMARY"}

    async def fake_send_email(to, s, b, **k):
        return {"success": True}

    monkeypatch.setattr(search_adapter, 'search_web', async_search)
    monkeypatch.setattr(browse_adapter, 'browse_website', async_browse)
    monkeypatch.setattr(ollama_adapter, 'call_gemma', fake_model)
    monkeypatch.setattr(email_adapter, 'send_email', fake_send_email)

    # Ensure DI wiring is initialized so the adapter manager is set and get instance
    svc = get_concierge_service()

    out = await svc.run_concierge_agent("Find sushi in Seattle", [])
    assert isinstance(out, str)
