from typing import Optional

from fastapi import Depends

import httpx

from .impl.ai_agent_service_impl import AiAgentServiceImpl
from .impl.concierge_agent_service import ConciergeAgentService
from ..adapters import ollama_adapter
from .. import config


# Module-level singletons
_ai_agent_service: Optional[AiAgentServiceImpl] = None
_http_client: Optional[httpx.Client] = None
_concierge_instance: Optional[ConciergeAgentService] = None


def get_http_client() -> httpx.Client:
    """Provide a singleton httpx client for adapters/services to use."""
    global _http_client
    if _http_client is None:
        _http_client = httpx.Client(timeout=10.0)
    return _http_client


def get_ai_agent_service() -> AiAgentServiceImpl:
    """Return a singleton AiAgentServiceImpl instance."""
    global _ai_agent_service
    if _ai_agent_service is None:
        _ai_agent_service = AiAgentServiceImpl()
        # Register any adapters defined by the codebase (idempotent)
        # always ensure "gemma" adapter is present as a fallback
        if "gemma3:4b" not in _ai_agent_service.list_adapters():
            _ai_agent_service.register_adapter("gemma3:4b", ollama_adapter.call_gemma)
        # Register adapters from config ADAPTERS mapping if present
        try:
            mappings = getattr(config, "get_adapter_mappings", lambda: {})()
            if isinstance(mappings, dict):
                for k, v in mappings.items():
                    # mappings should point to module.callable strings like 'package.module:callable'
                    if isinstance(v, str) and ":" in v:
                        mod_path, attr = v.split(":", 1)
                        try:
                            m = __import__(mod_path, fromlist=[attr])
                            fn = getattr(m, attr)
                            _ai_agent_service.register_adapter(k, fn)
                        except Exception:
                            # ignore registration failures here
                            pass
        except Exception:
            pass
    return _ai_agent_service


def get_concierge_service(ai_svc: AiAgentServiceImpl = Depends(get_ai_agent_service), http_client: httpx.Client = Depends(get_http_client)) -> ConciergeAgentService:
    """Return a ConciergeAgentService instance wired with adapter manager and http client."""
    global _concierge_instance
    if _concierge_instance is not None:
        return _concierge_instance

    # GemmaAgentService has a custom __new__ that doesn't accept kwargs, so
    # create the instance without triggering problematic __new__, then initialize
    inst = object.__new__(ConciergeAgentService)
    try:
        ConciergeAgentService.__init__(inst, adapter_manager=ai_svc, http_client=http_client)
    except TypeError:
        try:
            ConciergeAgentService.__init__(inst)
        except Exception:
            pass
        setattr(inst, "_adapter_manager", ai_svc)
        setattr(inst, "_http_client", http_client)

    _concierge_instance = inst
    return _concierge_instance


async def close_http_client() -> None:
    """Close the shared httpx client if it exists."""
    global _http_client
    try:
        if _http_client is not None:
            await _http_client.aclose()
    finally:
        _http_client = None
