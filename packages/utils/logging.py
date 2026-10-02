import logging
import sys
from typing import Any, Dict
import structlog


def drop_pii_processor(_: Any, __: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Spec §39 compliance: Sanitizes any accidental PII in log records."""
    pii_keys = {"phone", "caller_id", "name", "raw_audio", "auth_token", "password", "secret"}
    for key in list(event_dict.keys()):
        if any(pii in key.lower() for pii in pii_keys):
            event_dict[key] = "[REDACTED_PII]"
    return event_dict


def setup_logging(log_level: str = "INFO", json_format: bool = False) -> None:
    """Configures structured logging across standard library and structlog."""
    level = getattr(logging, log_level.upper(), logging.INFO)

    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        drop_pii_processor,
        structlog.processors.StackInfoRenderer(),
    ]

    if json_format:
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()

    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(level)


def get_logger(name: str = "saathi") -> structlog.BoundLogger:
    """Return a configured structured logger."""
    return structlog.get_logger(name)
