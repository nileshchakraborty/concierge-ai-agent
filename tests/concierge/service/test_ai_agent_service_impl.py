import uuid
import pytest

from concierge.service.di import get_ai_agent_service


@pytest.mark.asyncio
async def test_ai_agent_crud_and_adapters():
    svc = get_ai_agent_service()

    # CRUD
    rec = svc.create_agent({"name": "x", "type": "gemma"})
    assert "id" in rec
    aid = rec["id"]
    assert svc.get_agent(aid)["name"] == "x"
    assert svc.update_agent(aid, {"name": "y"})["name"] == "y"
    assert svc.delete_agent(aid) is True

    # adapters
    def dummy(prompt, **kwargs):
        return {"text": "ok"}

    svc.register_adapter('dummy', dummy)
    assert 'dummy' in svc.list_adapters()

    res = await svc.call_adapter('dummy', 'p')
    assert res == {"text": "ok"}
