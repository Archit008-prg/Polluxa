import logging
import json
import uuid
import sys
from datetime import datetime, timezone
from typing import Any, Dict

class StructuredJsonFormatter(logging.Formatter):
    """Custom JSON formatter producing machine-parseable logs with correlation IDs."""
    
    def __init__(self, service_name: str = "linkedin_analytics"):
        super().__init__()
        self.service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": self.service_name,
            "correlation_id": getattr(record, "correlation_id", str(uuid.uuid4())),
            "module": record.module,
            "line": record.lineno
        }
        
        # Attach exception info if present
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
            
        # Attach extra metadata passed via extra parameter
        if hasattr(record, "extra_data") and isinstance(record.extra_data, dict):
            log_obj["metadata"] = record.extra_data
            
        return json.dumps(log_obj)

def get_logger(name: str, correlation_id: str = None) -> logging.Logger:
    """Gets a logger configured with structured JSON output and correlation ID context."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredJsonFormatter())
        logger.addHandler(handler)
        logger.propagate = False
        
    return logger
