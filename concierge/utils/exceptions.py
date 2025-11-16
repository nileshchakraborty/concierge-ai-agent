class AdapterUnavailable(Exception):
    """Raised when a third-party adapter or service is unavailable.

    This is intentionally a plain exception (no FastAPI dependency) so it can be
    raised from adapters/services and mapped to HTTP 503 at the controller layer.
    """
    pass
