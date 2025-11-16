import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_third_party_ollama_failure(monkeypatch):
    import concierge.adapters.ollama_adapter as ollama_adapter
    from concierge.main import app

    async def _fake_ping(*a, **k):
        return {"ok": False, "detail": "ollama down"}

    monkeypatch.setattr(ollama_adapter, "ping", _fake_ping)

    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.get("/health/third_party")

    assert resp.status_code == 503
    body = resp.json()
    detail = body.get("detail")
    assert isinstance(detail, dict)
    services = detail.get("services")
    assert services.get("ollama") and services.get("ollama").get("ok") is False


@pytest.mark.asyncio
async def test_health_third_party_browse_failure(monkeypatch):
    import concierge.adapters.browse_adapter as browse_adapter
    from concierge.main import app

    async def _fake_browse_ping(*a, **k):
        return {"ok": False, "detail": "browse blocked"}

    monkeypatch.setattr(browse_adapter, "ping", _fake_browse_ping)

    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.get("/health/third_party")

    assert resp.status_code == 503
    body = resp.json()
    detail = body.get("detail")
    services = detail.get("services")
    assert services.get("browse") and services.get("browse").get("ok") is False


@pytest.mark.asyncio
async def test_concierge_query_503_when_browse_fails(monkeypatch):
    # Simulate a working search adapter and model selection, but browsing returns errors.
    import concierge.adapters.search_adapter as search_adapter
    import concierge.adapters.ollama_adapter as ollama_adapter
    import concierge.adapters.browse_adapter as browse_adapter
    from concierge.main import app

    # Make search return a minimal result with one organic link
    async def fake_search(query, client=None):
        return {"text": "Search Results", "organic": [{"link": "http://example.com", "title": "Example", "snippet": "example snippet"}]}

    # Model will pick the url
    async def fake_call_gemma(prompt, **kwargs):
        # For the pick-URLs prompt return the URL on a single line
        return {"text": "http://example.com"}

    # Browsing fails (returns an error string)
    async def fake_browse(url, client=None):
        return "Error browsing website http://example.com: blocked"

    monkeypatch.setattr(search_adapter, "search_web", fake_search)
    monkeypatch.setattr(ollama_adapter, "call_gemma", fake_call_gemma)
    monkeypatch.setattr(browse_adapter, "browse_website", fake_browse)

    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.post(
            "/concierge/query",
            json={"goal": "Find flights from Richmond, VA to Mumbai, IN", "history": []},
        )

    # Because browsing failed to return usable content, service should respond with 503
    assert resp.status_code == 503
