import time
import requests
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple, Optional
from config.settings import settings
from config.logging_config import get_logger

logger = get_logger("api_client")

class PolluxaApiClient:
    """Secure, idempotent API ingestion client with exponential backoff and rate-limit handling."""
    
    def __init__(self, base_url: str = None, token: str = None):
        self.base_url = (base_url or settings.POLLUXA_API_BASE_URL).rstrip("/")
        self.token = token or settings.POLLUXA_API_TOKEN
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "User-Agent": "LinkedInAnalyticsPipeline/1.0"
        }

    def _request_with_retry(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Executes GET request with exponential backoff and HTTP 429 rate-limit handling."""
        url = f"{self.base_url}{endpoint}"
        retries = 0
        backoff = settings.INITIAL_BACKOFF_SECONDS
        
        while retries <= settings.MAX_RETRIES:
            try:
                response = requests.get(url, headers=self.headers, params=params, timeout=10)
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", backoff * 2))
                    logger.warning(f"Rate limited (HTTP 429). Retrying in {retry_after}s... (Attempt {retries + 1}/{settings.MAX_RETRIES})")
                    time.sleep(retry_after)
                elif response.status_code >= 500:
                    logger.warning(f"Server error (HTTP {response.status_code}). Retrying in {backoff}s...")
                    time.sleep(backoff)
                else:
                    response.raise_for_status()
            except (requests.RequestException, Exception) as e:
                logger.warning(f"Request failed to {url}: {e}. Retrying in {backoff}s... (Attempt {retries + 1}/{settings.MAX_RETRIES})")
                time.sleep(backoff)
                
            retries += 1
            backoff *= 2.0
            
        raise RuntimeError(f"API request to {url} failed after {settings.MAX_RETRIES} retries.")

    def fetch_agents(self) -> List[Dict[str, Any]]:
        """Fetches registered LinkedIn Agents from portal."""
        try:
            res = self._request_with_retry("/agents")
            return res.get("data", [])
        except Exception as e:
            logger.error(f"Failed to fetch agents: {e}")
            raise e

    def fetch_campaigns(self) -> List[Dict[str, Any]]:
        """Fetches active campaigns from portal."""
        try:
            res = self._request_with_retry("/campaigns")
            return res.get("data", [])
        except Exception as e:
            logger.error(f"Failed to fetch campaigns: {e}")
            raise e

    def fetch_outreach_events(
        self,
        since_watermark: Optional[datetime] = None,
        limit: int = 500,
        simulate_429: bool = False,
        simulate_malformed: bool = False
    ) -> Tuple[List[Dict[str, Any]], datetime]:
        """Fetches incremental outreach events using watermark timestamp."""
        params = {"limit": limit}
        if since_watermark:
            params["since"] = since_watermark.isoformat()
        if simulate_429:
            params["simulate_429"] = "true"
        if simulate_malformed:
            params["simulate_malformed"] = "true"
            
        res = self._request_with_retry("/outreach/events", params=params)
        events = res.get("data", [])
        new_watermark_str = res.get("watermark", datetime.now(timezone.utc).isoformat())
        new_watermark = datetime.fromisoformat(new_watermark_str)
        
        return events, new_watermark
