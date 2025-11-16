import os
import logging
from logging.config import dictConfig


def configure_logging_from_env():
    level = os.environ.get("LOG_LEVEL", "INFO").upper()
    fmt = "%(asctime)s %(levelname)s %(name)s: %(message)s"
    json_mode = os.environ.get("LOG_FORMAT", "plain").lower() == "json"
    if json_mode:
        try:
            from pythonjsonlogger import jsonlogger

            config = {
                "version": 1,
                "disable_existing_loggers": False,
                "formatters": {"json": {"()": jsonlogger.JsonFormatter, "fmt": fmt}},
                "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "json", "level": level}},
                "root": {"handlers": ["console"], "level": level},
            }
            dictConfig(config)
            return
        except Exception:
            # fall back to plain
            pass

    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {"default": {"format": fmt}},
        "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "default", "level": level}},
        "root": {"handlers": ["console"], "level": level},
    }
    dictConfig(config)
