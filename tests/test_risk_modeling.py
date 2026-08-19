import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.models import Base, DimAgent, FactDailyAgentSummary
from src.modeling.capacity_optimizer import DailyCapacityOptimizer

class TestRiskModeling(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def tearDown(self):
        self.session.close()

    def test_capacity_optimizer_throttling(self):
        agent = DimAgent(
            agent_id="AGT-TEST",
            agent_name="Test Agent",
            account_age_tier="1+ Year",
            risk_classification="Minimal Risk",
            daily_invite_ceiling=30,
            daily_message_ceiling=60,
            status="Active",
            is_current=True
        )
        self.session.add(agent)
        self.session.commit()

        summary = FactDailyAgentSummary(
            agent_sk=agent.agent_sk,
            date_key=20260819,
            invites_sent=30,
            accepts_received=0,
            anomaly_score=2.8,
            risk_flag="Critical",
            recommended_invite_capacity=30,
            recommended_message_capacity=60
        )
        self.session.add(summary)
        self.session.commit()

        optimizer = DailyCapacityOptimizer(self.session)
        rec_invites, rec_messages = optimizer.optimize_agent_capacity(agent.agent_sk, summary.summary_sk)

        self.assertEqual(rec_invites, 12)
        self.assertEqual(summary.recommended_invite_capacity, 12)

if __name__ == "__main__":
    unittest.main()
