from typing import Dict, Any, Tuple
from sqlalchemy.orm import Session
from src.database.models import DimAgent, FactDailyAgentSummary
from config.settings import ACCOUNT_AGE_RISK_MATRIX
from config.logging_config import get_logger

logger = get_logger("capacity_optimizer")

class DailyCapacityOptimizer:
    """
    Calculates dynamic recommended daily capacity limits (invites & messages)
    per agent based on Part 1 tier ceilings and observed anomaly risk scores.
    """

    def __init__(self, db: Session):
        self.db = db

    def optimize_agent_capacity(self, agent_sk: int, latest_summary_sk: int) -> Tuple[int, int]:
        """
        Calculates risk-throttled capacity limits for the given agent summary.
        """
        agent = self.db.query(DimAgent).get(agent_sk)
        summary = self.db.query(FactDailyAgentSummary).get(latest_summary_sk)

        if not agent or not summary:
            return 30, 60

        tier_info = ACCOUNT_AGE_RISK_MATRIX.get(agent.account_age_tier, ACCOUNT_AGE_RISK_MATRIX["1+ Year"])
        base_invites = tier_info["daily_invites"]
        base_messages = tier_info["daily_messages"]

        anomaly_score = summary.anomaly_score
        risk_flag = summary.risk_flag

        # Throttle logic based on anomaly risk score
        if risk_flag == "Critical" or anomaly_score >= 2.5:
            multiplier = 0.40 # 60% reduction to safeguard account against shadow-banning
        elif risk_flag == "Warning" or anomaly_score >= 1.5:
            multiplier = 0.70 # 30% reduction
        else:
            multiplier = 1.00 # 100% capacity allowed

        rec_invites = max(1, int(base_invites * multiplier))
        rec_messages = max(2, int(base_messages * multiplier))

        summary.recommended_invite_capacity = rec_invites
        summary.recommended_message_capacity = rec_messages
        self.db.commit()

        logger.info(
            f"Optimized capacity for Agent '{agent.agent_name}' ({agent.account_age_tier}): "
            f"Invites={rec_invites}/{base_invites}, Messages={rec_messages}/{base_messages} (Multiplier={multiplier})"
        )
        return rec_invites, rec_messages
