import unittest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.models import Base, FactOutreachActivity
from src.pipeline.orchestrator import IngestionPipelineOrchestrator

class TestPipelineIdempotency(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def tearDown(self):
        self.session.close()

    def test_pipeline_idempotency_prevents_duplicates(self):
        test_events = [
            {
                "event_id": "TEST-EVT-IDEM-001",
                "agent_id": "AGT-001",
                "agent_name": "Test Agent",
                "lead_id": "LEAD-1",
                "campaign_id": "CMP-1",
                "action_type": "invite",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        ]

        orchestrator = IngestionPipelineOrchestrator(db_session=self.session)
        run1 = orchestrator.run_pipeline(raw_events=test_events)
        self.assertEqual(run1.rows_ingested, 1)
        
        count1 = self.session.query(FactOutreachActivity).filter_by(event_id="TEST-EVT-IDEM-001").count()
        self.assertEqual(count1, 1)

        # Second execution (exact duplicate payload)
        orchestrator2 = IngestionPipelineOrchestrator(db_session=self.session)
        run2 = orchestrator2.run_pipeline(raw_events=test_events)
        self.assertEqual(run2.rows_ingested, 0)
        
        count2 = self.session.query(FactOutreachActivity).filter_by(event_id="TEST-EVT-IDEM-001").count()
        self.assertEqual(count2, 1)

if __name__ == "__main__":
    unittest.main()
