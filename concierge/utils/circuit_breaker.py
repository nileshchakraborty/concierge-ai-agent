import time
import asyncio
import logging
from typing import Callable, Any
from ..utils.exceptions import AdapterUnavailable
from fastapi import HTTPException
from ..utils import metrics

logger = logging.getLogger(__name__)
class CircuitBreaker:
    """A small async-aware circuit breaker decorator.

    Behavior changes vs. earlier: when a short-circuit condition occurs, this
    implementation raises `fastapi.HTTPException(status_code=503, detail=...)`
    instead of returning an error dict. This ensures the HTTP status is
    propagated to API clients when adapters are unavailable.
    """

    def __init__(self, max_failures: int = 5, reset_timeout: int = 60, name: str | None = None):
        self.max_failures = int(max_failures)
        self.reset_timeout = int(reset_timeout)
        self.name = name or "circuit"
        self._failures = 0
        self._opened_at: float | None = None
        self._lock = asyncio.Lock()

    def _is_open(self) -> bool:
        if self._opened_at is None:
            return False
        # if reset timeout has passed, allow a trial
        if time.time() - self._opened_at >= self.reset_timeout:
            return False
        return True

    async def _record_failure(self) -> None:
        async with self._lock:
            self._failures += 1
            logger.warning("Circuit %s register failure %s/%s", self.name, self._failures, self.max_failures)
            if self._failures >= self.max_failures:
                self._opened_at = time.time()
                logger.error("Circuit %s opened", self.name)
                try:
                    metrics.incr(f"circuit.{self.name}.opened")
                except Exception:
                    pass

    async def _record_success(self) -> None:
        async with self._lock:
            if self._failures:
                logger.info("Circuit %s reset after success", self.name)
            self._failures = 0
            self._opened_at = None
            try:
                metrics.incr(f"circuit.{self.name}.reset")
            except Exception:
                pass

    def __call__(self, func: Callable[..., Any]) -> Callable[..., Any]:
        if asyncio.iscoroutinefunction(func):
            async def wrapper(*args, **kwargs):
                if self._is_open():
                    msg = f"Circuit {self.name} is open - short-circuiting"
                    logger.warning(msg)
                    # Raise AdapterUnavailable so callers (service/controller) map to HTTP 503
                    raise AdapterUnavailable(msg)
                try:
                    result = await func(*args, **kwargs)
                except Exception as e:
                    await self._record_failure()
                    logger.exception("Exception in circuit-wrapped function %s: %s", getattr(func, '__name__', str(func)), e)
                    # propagate original exception so upper layers can handle it
                    raise

                # If the function returns an error dict, treat it as a failure and raise
                if isinstance(result, dict) and result.get("error"):
                    await self._record_failure()
                    # signal adapter-level unavailability without importing FastAPI here
                    raise AdapterUnavailable(result.get("error"))
                else:
                    await self._record_success()
                return result

            return wrapper
        else:
            def sync_wrapper(*args, **kwargs):
                if self._is_open():
                    msg = f"Circuit {self.name} is open - short-circuiting"
                    logger.warning(msg)
                    raise HTTPException(status_code=503, detail=msg)
                try:
                    result = func(*args, **kwargs)
                except Exception:
                    # best effort sync recording
                    try:
                        asyncio.get_event_loop().create_task(self._record_failure())
                    except Exception:
                        logger.exception("Failed to schedule failure record for circuit %s", self.name)
                    raise

                if isinstance(result, dict) and result.get("error"):
                    try:
                        asyncio.get_event_loop().create_task(self._record_failure())
                    except Exception:
                        pass
                    raise HTTPException(status_code=503, detail=result.get("error"))
                else:
                    try:
                        asyncio.get_event_loop().create_task(self._record_success())
                    except Exception:
                        pass
                return result

            return sync_wrapper
