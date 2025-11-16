
from abc import ABC, abstractmethod
from typing import Any, Callable


class AiAgentService(ABC):
    """Abstract interface for AI agent services and adapter/plugin management.

    Implementations should provide CRUD for agents and a plugin registry for
    adapter callables to integrate different LLM backends (local or remote).
    """

    @abstractmethod
    def getAgent(self, input: dict) -> dict:
        pass

    @abstractmethod
    def listAgents(self) -> list[dict]:
        pass

    # Adapter / plugin management
    @abstractmethod
    def register_adapter(self, name: str, adapter: Callable[..., Any]) -> None:
        """Register an adapter callable under `name`. The adapter should accept (prompt, **kwargs)."""

    @abstractmethod
    def get_adapter(self, name: str) -> Callable[..., Any] | None:
        pass

    @abstractmethod
    def list_adapters(self) -> list[str]:
        pass

    @abstractmethod
    def call_adapter(self, name: str, prompt: str, **kwargs) -> Any:
        """Call a registered adapter by name and return its result."""