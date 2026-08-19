import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings:
    """Application settings with environment variable management."""
    def __init__(self):
        self.ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
        self.DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'data' / 'linkedin_analytics.db'}")
        self.POLLUXA_API_BASE_URL = os.getenv("POLLUXA_API_BASE_URL", "http://localhost:8000/api/v1")
        self.POLLUXA_API_TOKEN = os.getenv("POLLUXA_API_TOKEN", "mock_secure_bearer_token_polluxa_2026")
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        self.DQ_PASS_THRESHOLD = float(os.getenv("DQ_PASS_THRESHOLD", "0.90"))
        self.ALERT_WEBHOOK_URL = os.getenv("ALERT_WEBHOOK_URL", "http://localhost:8000/api/v1/alerts/webhook")
        self.MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
        self.INITIAL_BACKOFF_SECONDS = float(os.getenv("INITIAL_BACKOFF_SECONDS", "1.0"))
        self.BATCH_SIZE = int(os.getenv("BATCH_SIZE", "100"))

# Account Age Risk Matrix from Polluxa SOP Specification (Page 4)
ACCOUNT_AGE_RISK_MATRIX = {
    "< 1 Month": {
        "risk_classification": "Very High Risk",
        "daily_invites": 5,
        "daily_messages": 10
    },
    "1 Month": {
        "risk_classification": "High Risk",
        "daily_invites": 10,
        "daily_messages": 15
    },
    "2–6 Months": {
        "risk_classification": "Moderate Risk",
        "daily_invites": 15,
        "daily_messages": 25
    },
    "6–12 Months": {
        "risk_classification": "Low Risk",
        "daily_invites": 25,
        "daily_messages": 40
    },
    "1+ Year": {
        "risk_classification": "Minimal Risk",
        "daily_invites": 30,
        "daily_messages": 60
    }
}

settings = Settings()
