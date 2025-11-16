import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_adapter_unavailable_maps_to_503(monkeypatch):
    # Simulate circuit breaker open by monkeypatching the search adapter's ping to raise AdapterUnavailable
    import concierge.adapters.search_adapter as search_adapter
    from concierge.main import app
    from concierge.utils.exceptions import AdapterUnavailable

    async def fake_search(*a, **k):
        raise AdapterUnavailable("search provider down")

    monkeypatch.setattr(search_adapter, "search_web", fake_search)

    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.post(
            "/concierge/query",
            json={"goal": "Find flights from Richmond, VA to Mumbai, IN", "history": []},
        )

    assert resp.status_code == 503
    body = resp.json()
    # FastAPI error format: detail should contain the message
    assert "search provider down" in str(body.get("detail"))
