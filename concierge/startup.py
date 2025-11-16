"""Startup utilities for concierge app.

This module registers adapters defined in configuration into the
ConciergeAgentService adapter manager at application startup.
"""
from importlib import import_module
from typing import Dict
import traceback

from . import config
from .service.di import get_ai_agent_service
from .service.impl.concierge_agent_service import ConciergeAgentService


def _find_callable_in_module(mod):
    # Common entrypoint names adapters may expose
    candidates = ["call", "generate", "call_gemma", "__call__", "adapter"]
    for name in candidates:
        fn = getattr(mod, name, None)
        if callable(fn):
            return fn
    # If module itself is callable (unlikely), return it
    if callable(mod):
        return mod
    return None


def register_configured_adapters() -> Dict[str, str]:
    """Register adapters noted in configuration.

    Returns a dict of successfully registered adapters mapped to module path.
    """
    mappings = config.get_adapter_mappings()
    registered = {}
    if not mappings:
        return registered

    # Ensure the DI-provided ai agent service (and its adapter manager) is initialized
    ai_svc = get_ai_agent_service()
    mgr = ai_svc
    for name, module_path in mappings.items():
        try:
            mod = import_module(module_path)
            fn = _find_callable_in_module(mod)
            if fn is None:
                # couldn't find an entrypoint; skip
                continue
            mgr.register_adapter(name, fn)
            registered[name] = module_path
        except Exception as e:
            # Keep startup robust: print error and continue
            print(f"Failed to register adapter {name} from {module_path}: {e}")
            traceback.print_exc()

    return registered
