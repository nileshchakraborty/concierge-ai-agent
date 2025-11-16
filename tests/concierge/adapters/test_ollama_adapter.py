import importlib
import pytest


class MockResponse:
    def __init__(self, status_code=200, json_data=None):
        self.status_code = status_code
        self._json = json_data or {}

    def json(self):
        return self._json

    def raise_for_status(self):
        if not (200 <= self.status_code < 300):
            raise Exception(f"HTTP {self.status_code}")


@pytest.mark.asyncio
async def test_ollama_adapter(monkeypatch):
    from concierge.adapters import ollama_adapter
    importlib.reload(ollama_adapter)

    def fake_post(url, json=None, timeout=None):
        return MockResponse(status_code=200, json_data={"response": "ok"})

    class FakeAsyncClient:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, json=None, timeout=None):
            return fake_post(url, json=json, timeout=timeout)

    monkeypatch.setattr('concierge.adapters.ollama_adapter.httpx.AsyncClient', FakeAsyncClient)

    out = await ollama_adapter.call_gemma('prompt')
    assert isinstance(out, dict)
    assert out.get('text') == 'ok'
