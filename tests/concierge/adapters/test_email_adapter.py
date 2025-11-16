import importlib
import pytest


@pytest.mark.asyncio
async def test_email_adapter_no_config(monkeypatch):
    monkeypatch.delenv('SMTP_SERVER', raising=False)
    monkeypatch.delenv('SMTP_USERNAME', raising=False)
    monkeypatch.delenv('SMTP_PASSWORD', raising=False)
    monkeypatch.delenv('SENDER_EMAIL', raising=False)
    from concierge.adapters import email_adapter
    importlib.reload(email_adapter)

    res = await email_adapter.send_email('a@b.com', 's', 'b')
    assert res.get('success') is False
