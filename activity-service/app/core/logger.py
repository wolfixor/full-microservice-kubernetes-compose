"""Logging configuration for activity service."""

import json
import logging
import os
import sys
from datetime import datetime, timezone

from .config import settings
from .log_context import get_request_id


class JSONFormatter(logging.Formatter):
    """JSON log formatter that includes required ELK fields."""

    def format(self, record):
        log_record = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.")
            + f"{int(record.created % 1 * 1e6):06d}Z",
            "service": settings.APP_NAME,
            "level": record.levelname,
            "request_id": get_request_id(),
            "pod_name": os.environ.get("HOSTNAME", "unknown"),
            "message": record.getMessage(),
            "logger": record.name,
        }
        if record.exc_info and record.exc_info[0]:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record, ensure_ascii=False, default=str)


def setup_logging():
    """Configure JSON structured logging."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    logging.basicConfig(
        level=logging.INFO,
        handlers=[handler],
        force=True,
    )
