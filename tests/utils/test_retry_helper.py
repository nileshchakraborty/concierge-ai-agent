import pytest
import httpx


def test_retry_decorator_retries_and_succeeds(monkeypatch):
    from concierge.utils.retry import make_retry_decorator

    calls = {"count": 0}

    # create a retry decorator that retries twice and then succeeds
    dec = make_retry_decorator(retries_env=None, backoff_env=None, default_retries=3, default_backoff=0.01, exception_type=Exception)

    @dec
    async def flaky():
        calls["count"] += 1
        if calls["count"] < 3:
            raise Exception("transient")
        return "ok"

    import asyncio
    res = asyncio.get_event_loop().run_until_complete(flaky())
    assert res == "ok"
    assert calls["count"] == 3
