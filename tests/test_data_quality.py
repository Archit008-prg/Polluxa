import unittest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.models import Base
from src.quality.validator import DataQualityValidator

class TestDataQuality(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def tearDown(self):
        self.session.close()

    def test_data_quality_5point_validation(self):
        validator = DataQualityValidator(self.session)
        events = [
            {
                "event_id": "CLEAN-01",
                "agent_id": "AGT-001",
                "lead_id": "LEAD-01",
                "campaign_id": "CMP-01",
                "action_type": "invite",
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            {
                "event_id": "BAD-01",
                "agent_id": None,
                "lead_id": "LEAD-02",
                "campaign_id": "CMP-01",
                "action_type": "invite",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        ]

        valid, dead_letters, metrics = validator.validate_batch(events)
        self.assertEqual(len(valid), 1)
        self.assertEqual(len(dead_letters), 1)
        self.assertEqual(metrics["completeness"], 0.5)

if __name__ == "__main__":
    unittest.main()
