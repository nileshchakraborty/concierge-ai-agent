from concierge.service.impl.gemma_agent_service import GemmaAgentService


def test_gemma_agent_singleton():
    # The implementation in the repo expects a class-level `_instance` field.
    # Ensure a sensible `_instance` exists so instantiation returns an object.
    if not hasattr(GemmaAgentService, '_instance'):
        GemmaAgentService._instance = object.__new__(GemmaAgentService)

    a = GemmaAgentService()
    b = GemmaAgentService()
    assert a is GemmaAgentService._instance
    assert b is GemmaAgentService._instance
