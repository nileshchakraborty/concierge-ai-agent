"""FastAPI entrypoint for the Concierge agent.

This file provides a Pydantic request/response model and a thin controller
that delegates orchestration to `ConciergeAgentService` (adapter pattern).

It intentionally keeps the HTTP layer thin — adapters and service logic
live in `concierge.adapters` and `concierge.service.impl` respectively.
"""

from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .utils.logging_config import configure_logging_from_env
import logging

from .controller.concierge_agent_controller import router as concierge_router
from . import startup


app = FastAPI(title="Concierge Agent")


def configure_logging():
    level = os.environ.get("LOG_LEVEL", "INFO").upper()
    # Default console formatter
    fmt = "%(asctime)s %(levelname)s %(name)s: %(message)s"
    json_mode = os.environ.get("LOG_FORMAT", "plain").lower() == "json"
    if json_mode:
        try:
            from pythonjsonlogger import jsonlogger

            formatter = jsonlogger.JsonFormatter(fmt)
            config = {
                "version": 1,
                "disable_existing_loggers": False,
                "handlers": {
                    "console": {
                        "class": "logging.StreamHandler",
                        "formatter": "json",
                        "level": level,
                    }
                },
                "formatters": {"json": {"()": jsonlogger.JsonFormatter, "fmt": fmt}},
                "root": {"handlers": ["console"], "level": level},
            }
            dictConfig(config)
            return
        except Exception:
            # Fallback to plain formatter if json logger isn't available
            pass

    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {"default": {"format": fmt}},
        "handlers": {
            "console": {"class": "logging.StreamHandler", "formatter": "default", "level": level}
        },
        "root": {"handlers": ["console"], "level": level},
    }
    dictConfig(config)

# Allow simple CORS for local testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"status": "ok", "service": "concierge"}


# Include controller router (has /concierge/query and /agents CRUD)
app.include_router(concierge_router)


@app.on_event("startup")
def _register_adapters_on_startup():
    # Configure logging early so adapters and other modules log consistently
    configure_logging_from_env()
    registered = startup.register_configured_adapters()
    if registered:
        logging.getLogger(__name__).info("Registered adapters: %s", registered)


@app.on_event("shutdown")
async def _shutdown_close_http_client():
    try:
        # close the shared http client from DI
        from .service import di as di_module
        await di_module.close_http_client()
    except Exception:
        pass


def main():
    import uvicorn

    uvicorn.run("concierge.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
