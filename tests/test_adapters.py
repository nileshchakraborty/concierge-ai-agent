import os
from types import SimpleNamespace

import pytest

# These top-level adapter tests are duplicates of the more complete
# `tests/concierge/` adapter tests which use async fixtures. Skip them
# to avoid conflicts while the codebase uses async adapters.
pytest.skip("Top-level adapter tests skipped; use tests/concierge/", allow_module_level=True)


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


def test_search_adapter_returns_text(monkeypatch):
    # Ensure the adapter sees an API key (adapter reads env at import time)
    monkeypatch.setenv('SERPER_API_KEY', 'fake-key')
    from concierge.adapters import search_adapter
    # Reload module in case it was imported earlier when env var wasn't set
    import pytest

    # Duplicate tests removed — keep mirrored tests under tests/concierge/
    pytest.skip("Duplicate top-level tests removed; use tests/concierge/", allow_module_level=True)
    def fake_get(url, headers=None, timeout=None):
        return MockResponse(status_code=200, text=html.decode('utf-8'), content=html)

    monkeypatch.setattr('requests.get', fake_get)

    result = browse_adapter.browse_website("http://example.com")
    assert "Hello world" in result


def test_ollama_adapter_parses_response(monkeypatch):
    from concierge.adapters import ollama_adapter

    def fake_post(url, json=None, timeout=None):
        return MockResponse(status_code=200, json_data={"response": "it works"})

    monkeypatch.setattr('requests.post', fake_post)
    resp = ollama_adapter.call_gemma("prompt")
    assert isinstance(resp, dict)
    assert resp.get("text") == "it works"


def test_email_adapter_no_config(monkeypatch):
    from concierge.adapters import email_adapter

    # Ensure env vars are not set
    monkeypatch.delenv('SMTP_SERVER', raising=False)
    monkeypatch.delenv('SMTP_USERNAME', raising=False)
    monkeypatch.delenv('SMTP_PASSWORD', raising=False)
    monkeypatch.delenv('SENDER_EMAIL', raising=False)

    result = email_adapter.send_email('a@b.com', 'subj', 'body')
    assert result.get('success') is False

