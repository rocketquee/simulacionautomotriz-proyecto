"""Structured logging with correlation identifiers.

The platform emits machine-readable JSON by default so that logs can be shipped
to an observability backend without a parsing pipeline. A plain text formatter
is available for local development.
"""

from __future__ import annotations

import json
import logging
import sys
import threading
from contextvars import ContextVar, Token
from datetime import UTC, datetime
from typing import Any

from suspension_sim.core.schemas import LoggingSettings

_REQUEST_ID: ContextVar[str | None] = ContextVar("request_id", default=None)
_CONFIGURATION_LOCK = threading.Lock()
_CONFIGURED = False

_STANDARD_ATTRIBUTES = frozenset(logging.LogRecord("", 0, "", 0, "", (), None).__dict__)


def set_request_id(request_id: str) -> Token[str | None]:
    return _REQUEST_ID.set(request_id)


def reset_request_id(token: Token[str | None]) -> None:
    _REQUEST_ID.reset(token)


class JsonFormatter(logging.Formatter):
    """Render log records as a single JSON object per line."""

    def __init__(self, *, include_timestamps: bool = True) -> None:
        super().__init__()
        self._include_timestamps = include_timestamps

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if self._include_timestamps:
            payload["timestamp"] = datetime.fromtimestamp(record.created, tz=UTC).isoformat()

        request_id = _REQUEST_ID.get()
        if request_id is not None:
            payload["request_id"] = request_id

        for key, value in record.__dict__.items():
            if key not in _STANDARD_ATTRIBUTES and not key.startswith("_"):
                payload[key] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)


class TextFormatter(logging.Formatter):
    """Compact human-readable formatter for local runs."""

    def __init__(self, *, include_timestamps: bool = True) -> None:
        fmt = "%(asctime)s %(levelname)-8s %(name)s %(message)s" if include_timestamps else (
            "%(levelname)-8s %(name)s %(message)s"
        )
        super().__init__(fmt=fmt, datefmt="%H:%M:%S")


def configure_logging(settings: LoggingSettings) -> None:
    """Install a single stdout handler exactly once per process."""

    global _CONFIGURED
    with _CONFIGURATION_LOCK:
        if _CONFIGURED:
            logging.getLogger().setLevel(settings.level)
            for noisy_logger in ("matplotlib", "matplotlib.font_manager", "PIL", "fontTools"):
                logging.getLogger(noisy_logger).setLevel(logging.WARNING)
            return

        handler = logging.StreamHandler(stream=sys.stderr)
        formatter: logging.Formatter
        if settings.json_output:
            formatter = JsonFormatter(include_timestamps=settings.include_timestamps)
        else:
            formatter = TextFormatter(include_timestamps=settings.include_timestamps)
        handler.setFormatter(formatter)

        root = logging.getLogger()
        root.handlers.clear()
        root.addHandler(handler)
        root.setLevel(settings.level)
        for noisy_logger in ("matplotlib", "matplotlib.font_manager", "PIL", "fontTools"):
            logging.getLogger(noisy_logger).setLevel(logging.WARNING)
        _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
