import asyncio
import pytest
from concierge.utils.exceptions import AdapterUnavailable


@pytest.mark.asyncio
async def test_circuit_breaker_opens_and_raises():
    from concierge.utils.circuit_breaker import CircuitBreaker

    cb = CircuitBreaker(max_failures=2, reset_timeout=1, name="testcb")

    # function that returns error dict
    async def failing():
        return {"error": "down"}

    wrapped = cb(failing)

    # first call registers failure and AdapterUnavailable is raised
    with pytest.raises(AdapterUnavailable):
        await wrapped()

    # second call should open the circuit and raise AdapterUnavailable
    with pytest.raises(AdapterUnavailable):
        await wrapped()

    # circuit should now be open and raise immediately
    with pytest.raises(AdapterUnavailable):
        await wrapped()

    # wait for reset timeout and ensure call allowed again
    await asyncio.sleep(1.1)

    async def success():
        return {"ok": True}

    wrapped_success = cb(success)
    # should not raise and should return success dict
    res = await wrapped_success()
    assert isinstance(res, dict) and res.get("ok")
