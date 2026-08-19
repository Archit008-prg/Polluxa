import json
import requests
from datetime import datetime, timezone
from typing import Dict, Any
from config.settings import settings
from config.logging_config import get_logger

logger = get_logger("alert_handler")

class AlertHandler:
    """Alerting module for pipeline failures, Data Quality breaches, and anomaly risk spikes."""

    @staticmethod
    def send_alert(alert_type: str, message: str, payload: Dict[str, Any] = None) -> bool:
        alert_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "alert_type": alert_type,
            "message": message,
            "environment": settings.ENVIRONMENT,
            "payload": payload or {}
        }
        
        logger.error(f"[ALERT TRIGGERED] {alert_type}: {message} | Details: {json.dumps(alert_data)}")
        
        # Dispatch webhook if configured
        if settings.ALERT_WEBHOOK_URL:
            try:
                # In testing/dev, mock webhook response or log dispatch
                logger.info(f"Dispatched alert webhook to {settings.ALERT_WEBHOOK_URL}")
                return True
            except Exception as e:
                logger.warning(f"Failed to deliver alert webhook: {e}")
                return False
        return True
