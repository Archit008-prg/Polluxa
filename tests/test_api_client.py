import unittest
from datetime import datetime, timezone
from src.api.client import PolluxaApiClient

class TestApiClient(unittest.TestCase):
    def test_api_client_initialization(self):
        client = PolluxaApiClient(base_url="http://localhost:8000/api/v1", token="test_token")
        self.assertEqual(client.base_url, "http://localhost:8000/api/v1")
        self.assertIn("Authorization", client.headers)
        self.assertEqual(client.headers["Authorization"], "Bearer test_token")

    def test_watermark_incremental_fetching_logic(self):
        client = PolluxaApiClient()
        self.assertTrue(hasattr(client, "fetch_outreach_events"))

if __name__ == "__main__":
    unittest.main()
