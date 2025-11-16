from .gemma_agent_service import GemmaAgentService
from ..ai_agent_service import AiAgentService
import uuid
import inspect


class AiAgentServiceImpl(AiAgentService):
    """A simple in-memory implementation for agent CRUD used by the controller.

    This is intentionally lightweight — it stores agents in a module-level dict.
    For production use, replace with a persistence-backed implementation.
    """

    _store: dict = {}

    def __init__(self):
        # Ensure store exists
        if not hasattr(self.__class__, "_store"):
            self.__class__._store = {}

    def create_agent(self, data: dict) -> dict:
        agent_id = str(uuid.uuid4())
        record = {"id": agent_id, **data}
        self.__class__._store[agent_id] = record
        return record

    def get_agent(self, agent_id: str) -> dict | None:
        return self.__class__._store.get(agent_id)

    def update_agent(self, agent_id: str, updates: dict) -> dict | None:
        if agent_id not in self.__class__._store:
            return None
        self.__class__._store[agent_id].update(updates)
        return self.__class__._store[agent_id]

    def delete_agent(self, agent_id: str) -> bool:
        return self.__class__._store.pop(agent_id, None) is not None

    # Keep compatibility names for existing abstract methods
    def getAgent(self, input: dict) -> AiAgentService:
        if input.get("type") == "gemma":
            return GemmaAgentService()
        return None

    def listAgents(self) -> list[dict]:
        return list(self.__class__._store.values())

    # snake_case aliases expected by controllers/tests
    def list_agents(self) -> list[dict]:
        return self.listAgents()

    # Adapter/plugin registry implementation
    _adapters: dict = {}

    def register_adapter(self, name: str, adapter):
        """Register an adapter callable or object under `name`."""
        self.__class__._adapters[name] = adapter

    def get_adapter(self, name: str):
        return self.__class__._adapters.get(name)

    def list_adapters(self) -> list[str]:
        return list(self.__class__._adapters.keys())

    async def call_adapter(self, name: str, prompt: str, **kwargs):
        """Call a registered adapter. Support adapter being a callable or module with a call function.

        Await coroutine adapters and call synchronous adapters directly.
        """
        adapter = self.get_adapter(name)
        if adapter is None:
            raise ValueError(f"Adapter '{name}' not registered")

        async def _maybe_await(fn, *a, **kw):
            res = fn(*a, **kw)
            if inspect.isawaitable(res):
                return await res
            return res

        # If adapter is a callable, call it
        if callable(adapter):
            return await _maybe_await(adapter, prompt, **kwargs)

        # If adapter is a module/object with known entrypoints, try common names
        for attr in ("call", "__call__", "call_gemma", "generate", "send"):
            fn = getattr(adapter, attr, None)
            if callable(fn):
                return await _maybe_await(fn, prompt, **kwargs)

        raise TypeError("Adapter does not expose a callable entrypoint")
