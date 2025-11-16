import importlib
from types import SimpleNamespace
import pytest


class MockResponse:
    def __init__(self, status_code=200, json_data=None, text="", content=b""):
        self.status_code = status_code
        self._json = json_data or {}
        self.text = text
        self.content = content

    def json(self):
        return self._json

    def raise_for_status(self):
        if not (200 <= self.status_code < 300):
            raise Exception(f"HTTP {self.status_code}")


@pytest.mark.asyncio
async def test_search_adapter_human_text(monkeypatch):
    monkeypatch.setenv('SERPER_API_KEY', 'fake-key')
    from concierge.adapters import search_adapter
    importlib.reload(search_adapter)

    def fake_post(url, headers=None, json=None, timeout=None):
        data = {"organic": [{"title": "T1", "link": "http://a", "snippet": "S1"}]}
        return MockResponse(status_code=200, json_data=data, text=str(data))

    class FakeAsyncClient:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, headers=None, json=None, timeout=None):
            return fake_post(url, headers=headers, json=json, timeout=timeout)

    monkeypatch.setattr('concierge.adapters.search_adapter.httpx.AsyncClient', FakeAsyncClient)

    res = await search_adapter.search_web("test query")
    assert isinstance(res, dict)
    assert "text" in res
    assert "Search Results" in res["text"]
