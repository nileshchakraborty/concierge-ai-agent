import importlib
import pytest


class MockResponse:
    def __init__(self, status_code=200, text="", content=b""):
        self.status_code = status_code
        self.text = text
        self.content = content

    def raise_for_status(self):
        if not (200 <= self.status_code < 300):
            raise Exception(f"HTTP {self.status_code}")


@pytest.mark.asyncio
async def test_browse_adapter_text(monkeypatch):
    monkeypatch.setenv('DUMMY', '1')
    from concierge.adapters import browse_adapter
    importlib.reload(browse_adapter)
    html = b"<html><body><p>Hello Test</p><script>ignore</script></body></html>"

    def fake_get(url, headers=None, timeout=None):
        return MockResponse(status_code=200, text=html.decode('utf-8'), content=html)

    class FakeAsyncClient:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, url, headers=None, timeout=None):
            return fake_get(url, headers=headers, timeout=timeout)

    monkeypatch.setattr('concierge.adapters.browse_adapter.httpx.AsyncClient', FakeAsyncClient)

    out = await browse_adapter.browse_website('http://example')
    assert 'Hello Test' in out
