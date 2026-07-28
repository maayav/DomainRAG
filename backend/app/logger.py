"""Structured JSON logger."""
import json
import logging
import sys
from datetime import datetime, timezone


class StructuredLogger:
    def __init__(self, name: str, level: str = "INFO"):
        self._logger = logging.getLogger(name)
        self._logger.setLevel(getattr(logging, level.upper(), logging.INFO))
        self._logger.handlers.clear()
        handler = logging.StreamHandler(sys.stdout)

        def emit(record):
            entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
            }
            if hasattr(record, "extra"):
                entry.update(record.extra)
            sys.stdout.write(json.dumps(entry) + "\n")

        handler.emit = emit
        self._logger.addHandler(handler)

    def info(self, msg: str, extra: dict | None = None):
        self._logger.info(msg, extra={"extra": extra} if extra else None)

    def warning(self, msg: str, extra: dict | None = None):
        self._logger.warning(msg, extra={"extra": extra} if extra else None)

    def error(self, msg: str, extra: dict | None = None):
        self._logger.error(msg, extra={"extra": extra} if extra else None)

    def debug(self, msg: str, extra: dict | None = None):
        self._logger.debug(msg, extra={"extra": extra} if extra else None)