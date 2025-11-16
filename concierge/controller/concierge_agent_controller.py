from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..service.impl.concierge_agent_service import ConciergeAgentService
from ..service.di import get_ai_agent_service, get_concierge_service
from ..adapters import search_adapter, ollama_adapter, browse_adapter
import asyncio
from fastapi import status as http_status
from ..utils.exceptions import AdapterUnavailable


router = APIRouter()


class ConciergeRequest(BaseModel):
    goal: str
    history: List[str] = []


class ConciergeResponse(BaseModel):
    result: str


@router.post("/concierge/query", response_model=ConciergeResponse)
async def query_concierge(request: ConciergeRequest, svc: ConciergeAgentService = Depends(get_concierge_service)):
    try:
        result = await svc.run_concierge_agent(request.goal, request.history)
        return ConciergeResponse(result=result)
    except HTTPException:
        # Preserve HTTPException responses from lower layers (e.g., adapters/services)
        raise
    except AdapterUnavailable as e:
        # Map adapter-level unavailability to HTTP 503 so clients see dependency issues
        raise HTTPException(status_code=http_status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Simple Agents CRUD ---


class AgentCreate(BaseModel):
    name: str
    type: str
    config: dict = {}


class AgentUpdate(BaseModel):
    name: str | None = None
    config: dict | None = None


@router.post("/agents")
def create_agent(payload: AgentCreate, svc = Depends(get_ai_agent_service)):
    agent = svc.create_agent(payload.dict())
    return agent



@router.get("/health/third_party")
async def health_third_party():
    """Diagnose third-party connectivity: search provider, ollama, and outbound browsing."""
    # run pings concurrently
    tasks = [
        search_adapter.ping(),
        ollama_adapter.ping(),
        browse_adapter.ping(),
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    status_map = {}
    overall_ok = True
    keys = ("search", "ollama", "browse")
    for k, r in zip(keys, results):
        if isinstance(r, Exception):
            status_map[k] = {"ok": False, "detail": str(r)}
            overall_ok = False
        else:
            status_map[k] = r
            if not r.get("ok"):
                overall_ok = False

    if overall_ok:
        return {"ok": True, "services": status_map}
    # At least one service failed — return 503 so callers know third-party dependency is degraded
    raise HTTPException(status_code=http_status.HTTP_503_SERVICE_UNAVAILABLE, detail={"ok": False, "services": status_map})


@router.get("/agents")
def list_agents(svc = Depends(get_ai_agent_service)):
    return svc.list_agents()


@router.get("/agents/{agent_id}")
def get_agent(agent_id: str, svc = Depends(get_ai_agent_service)):
    agent = svc.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.put("/agents/{agent_id}")
def update_agent(agent_id: str, payload: AgentUpdate, svc = Depends(get_ai_agent_service)):
    updated = svc.update_agent(agent_id, payload.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Agent not found")
    return updated


@router.delete("/agents/{agent_id}")
def delete_agent(agent_id: str, svc = Depends(get_ai_agent_service)):
    ok = svc.delete_agent(agent_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"deleted": True}
