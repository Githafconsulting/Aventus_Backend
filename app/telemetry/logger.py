"""
Structured JSON logging configuration.
All logs include correlation IDs and are formatted for CloudWatch/ELK compatibility.
"""
import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional


class JSONFormatter(logging.Formatter):
    """
    Custom formatter that outputs logs as JSON.
    Compatible with CloudWatch, ELK, and other log aggregators.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add extra fields if present
        if hasattr(record, "correlation_id"):
            log_data["correlation_id"] = record.correlation_id

        # Add any extra attributes passed to the logger
        if record.__dict__.get("extra"):
            log_data.update(record.__dict__["extra"])

        # Add extra fields from the record
        for key, value in record.__dict__.items():
            if key not in (
                "name", "msg", "args", "created", "filename", "funcName",
                "levelname", "levelno", "lineno", "module", "msecs",
                "pathname", "process", "processName", "relativeCreated",
                "stack_info", "exc_info", "exc_text", "thread", "threadName",
                "extra", "message", "correlation_id"
            ):
                if not key.startswith("_"):
                    log_data[key] = value

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add location info
        log_data["location"] = {
            "file": record.filename,
            "function": record.funcName,
            "line": record.lineno,
        }

        return json.dumps(log_data, default=str)


class ContextAdapter(logging.LoggerAdapter):
    """
    Logger adapter that automatically includes context in log messages.
    """

    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        # Merge extra context
        extra = kwargs.get("extra", {})
        if self.extra:
            extra.update(self.extra)
        kwargs["extra"] = extra
        return msg, kwargs


def setup_logging(
    level: str = "INFO",
    json_format: bool = True,
) -> None:
    """
    Configure application logging.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: Whether to use JSON formatting
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers
    root_logger.handlers = []

    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, level.upper()))

    if json_format:
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        ))

    root_logger.addHandler(handler)

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str, **context) -> ContextAdapter:
    """
    Get a logger instance with optional context.

    Args:
        name: Logger name (usually __name__)
        **context: Additional context to include in all logs

    Returns:
        ContextAdapter logger instance

    Example:
        logger = get_logger(__name__, service="contractor")
        logger.info("Created contractor", extra={"contractor_id": 123})
    """
    logger = logging.getLogger(name)
    return ContextAdapter(logger, context)


# Default logger
logger = get_logger("aventus")
