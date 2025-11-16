from fastapi.testclient import TestClient
from concierge.main import app


def test_endpoints(monkeypatch):
    client = TestClient(app)

    from concierge.adapters import search_adapter, browse_adapter, ollama_adapter, email_adapter
    async def async_search(q, **k):
        return {"text": "results", "organic": [{"link": "http://a"}]}

    async def async_browse(u, **k):
        return "content a"

    async def async_gemma(p, **k):
        return {"text": "SUMMARY"}

    monkeypatch.setattr(search_adapter, 'search_web', async_search)
    monkeypatch.setattr(browse_adapter, 'browse_website', async_browse)
    monkeypatch.setattr(ollama_adapter, 'call_gemma', async_gemma)
    monkeypatch.setattr(email_adapter, 'send_email', lambda to, s, b, **k: {"success": True})

    r = client.post('/concierge/query', json={"goal": "Find sushi", "history": []})
    assert r.status_code == 200
    assert 'result' in r.json()
