import os
from typing import Type
import httpx
from tenacity import retry, wait_random_exponential, stop_after_attempt, retry_if_exception_type


def make_retry_decorator(
    retries_env: str | None = None,
    backoff_env: str | None = None,
    default_retries: int = 3,
    default_backoff: float = 0.5,
    exception_type: Type[BaseException] = httpx.HTTPError,
):
    """Return a tenacity `retry` decorator configured via optional env var names.

    - `retries_env`: environment variable name containing integer attempts
    - `backoff_env`: environment variable name containing base multiplier
    - `exception_type`: exception type to retry on (default httpx.HTTPError)
    """
    retries = int(os.environ.get(retries_env, default_retries)) if retries_env else default_retries
    backoff = float(os.environ.get(backoff_env, default_backoff)) if backoff_env else default_backoff

    return retry(
        reraise=True,
        stop=stop_after_attempt(retries),
        wait=wait_random_exponential(multiplier=backoff),
        retry=retry_if_exception_type(exception_type),
    )
