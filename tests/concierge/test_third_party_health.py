import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_concierge_query_503_on_search_missing(monkeypatch):
    # Ensure the search adapter behaves as if the API key is missing
    import concierge.adapters.search_adapter as search_adapter
    from concierge.main import app

    monkeypatch.setattr(search_adapter, "SERPER_API_KEY", None)

    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.post(
            "/concierge/query",
            json={"goal": "Find flights from Richmond, VA to Mumbai, IN", "history": []},
        )

    assert resp.status_code == 503


@pytest.mark.asyncio
async def test_health_third_party_reports_503_when_search_down(monkeypatch):
    # When the search adapter reports missing API key, the health endpoint should report degraded status
    import concierge.adapters.search_adapter as search_adapter
    from concierge.main import app

    monkeypatch.setattr(search_adapter, "SERPER_API_KEY", None)

    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.get("/health/third_party")

    assert resp.status_code == 503
    body = resp.json()
    # FastAPI error response should include the detail object with per-service results
    assert isinstance(body, dict)
    detail = body.get("detail")
    assert isinstance(detail, dict)
    services = detail.get("services")
    assert services is not None
    assert services.get("search") and services.get("search").get("ok") is False
