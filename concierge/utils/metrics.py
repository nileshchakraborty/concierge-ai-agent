import threading
import time
import logging
from typing import Dict

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_counters: Dict[str, int] = {}


def incr(key: str, amount: int = 1) -> None:
    with _lock:
        _counters[key] = _counters.get(key, 0) + int(amount)


def get_counter(key: str) -> int:
    with _lock:
        return _counters.get(key, 0)


def dump_metrics() -> Dict[str, int]:
    with _lock:
        return dict(_counters)


def reset_metrics() -> None:
    with _lock:
        _counters.clear()
