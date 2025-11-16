import os
from pathlib import Path
from typing import Dict

# Load environment variables from .env files if present (project root and concierge/)
try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None

_root_env = Path(__file__).parent.parent / ".env"
_concierge_env = Path(__file__).parent / ".env"
if load_dotenv:
    if _root_env.exists():
        load_dotenv(dotenv_path=_root_env)
    if _concierge_env.exists():
        load_dotenv(dotenv_path=_concierge_env)


def _read_properties(path: Path) -> Dict[str, str]:
    props: Dict[str, str] = {}
    if not path.exists():
        return props
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, v = line.split("=", 1)
            props[k.strip()] = v.strip()
    return props


# Priority: environment variable overrides properties file
DEFAULT_AI_ADAPTER = os.environ.get("DEFAULT_AI_ADAPTER")

if DEFAULT_AI_ADAPTER is None:
    props_path = Path(__file__).parent / "config.properties"
    props = _read_properties(props_path)
    DEFAULT_AI_ADAPTER = props.get("DEFAULT_AI_ADAPTER", "gemma3:4b")


def get_adapter_mappings() -> dict:
    """Return adapter mappings from env or properties.

    Expected format (env or properties):
      ADAPTERS=name=module.path,name2=module2.path

    Example:
      ADAPTERS=openai=concierge.adapters.openai_adapter,anthropic=concierge.adapters.anthropic_adapter
    """
    # First check env var
    raw = os.environ.get("ADAPTERS")
    if not raw:
        props_path = Path(__file__).parent / "config.properties"
        props = _read_properties(props_path)
        raw = props.get("ADAPTERS")

    mappings: dict = {}
    if not raw:
        return mappings

    for part in raw.split(','):
        if not part.strip():
            continue
        if '=' in part:
            name, mod = part.split('=', 1)
            mappings[name.strip()] = mod.strip()
        elif ':' in part:
            name, mod = part.split(':', 1)
            mappings[name.strip()] = mod.strip()
        else:
            # If only module path provided, use the module's basename as name
            mod = part.strip()
            name = mod.split('.')[-1]
            mappings[name] = mod

    return mappings
