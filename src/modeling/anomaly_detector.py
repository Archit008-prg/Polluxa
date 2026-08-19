import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from src.database.models import FactDailyAgentSummary
from config.logging_config import get_logger

logger = get_logger("anomaly_detector")

class RiskAnomalyDetector:
    """
    Statistical risk model using 7-day rolling Z-Score & Moving Standard Deviation
    to detect hidden risk signals (acceptance-rate collapse, reply decay, ghosting patterns).
    """

    def __init__(self, db: Session):
        self.db = db

    def analyze_agent_performance(self, agent_sk: int, window_days: int = 7) -> List[Dict[str, Any]]:
        """
        Analyzes historical daily summaries for an agent and updates anomaly scores and risk flags.
        """
        summaries = (
            self.db.query(FactDailyAgentSummary)
            .filter(FactDailyAgentSummary.agent_sk == agent_sk)
            .order_by(FactDailyAgentSummary.date_key.asc())
            .all()
        )

        if not summaries:
            return []

        df = pd.DataFrame([
            {
                "summary_sk": s.summary_sk,
                "date_key": s.date_key,
                "invites_sent": s.invites_sent,
                "accepts_received": s.accepts_received,
                "messages_sent": s.messages_sent,
                "replies_received": s.replies_received,
                "ghosted_count": s.ghosted_count,
                "acceptance_rate": s.acceptance_rate,
                "reply_rate": s.reply_rate
            }
            for s in summaries
        ])

        if len(df) < 3:
            # Not enough baseline data for standard deviation; assign low baseline risk
            results = []
            for s in summaries:
                s.anomaly_score = 0.0
                s.risk_flag = "Normal"
                results.append({"summary_sk": s.summary_sk, "score": 0.0, "flag": "Normal"})
            self.db.commit()
            return results

        # Compute rolling statistics (7-day window)
        rolling_acc_mean = df["acceptance_rate"].rolling(window=window_days, min_periods=1).mean()
        rolling_acc_std = df["acceptance_rate"].rolling(window=window_days, min_periods=1).std().fillna(0.01)

        rolling_rep_mean = df["reply_rate"].rolling(window=window_days, min_periods=1).mean()
        rolling_rep_std = df["reply_rate"].rolling(window=window_days, min_periods=1).std().fillna(0.01)

        # Z-Scores
        acc_zscore = (rolling_acc_mean - df["acceptance_rate"]) / (rolling_acc_std + 1e-5) # Collapse when positive drop
        rep_zscore = (rolling_rep_mean - df["reply_rate"]) / (rolling_rep_std + 1e-5) # Reply decay
        
        # Ghosting Ratio Penalty
        ghosting_ratio = df["ghosted_count"] / (df["invites_sent"] + 1e-5)

        # Composite Anomaly Score: 50% Acceptance Collapse + 30% Reply Decay + 20% Ghosting Ratio
        composite_scores = (np.maximum(0, acc_zscore) * 0.50) + (np.maximum(0, rep_zscore) * 0.30) + (ghosting_ratio * 0.20)
        
        results = []
        for idx, row in df.iterrows():
            score = float(round(composite_scores.iloc[idx], 2))
            
            if score >= 2.5 or row["acceptance_rate"] < 0.05:
                flag = "Critical"
            elif score >= 1.5 or row["acceptance_rate"] < 0.15:
                flag = "Warning"
            else:
                flag = "Normal"

            # Update DB model
            summary_obj = self.db.query(FactDailyAgentSummary).get(int(row["summary_sk"]))
            if summary_obj:
                summary_obj.anomaly_score = score
                summary_obj.risk_flag = flag

            results.append({
                "summary_sk": int(row["summary_sk"]),
                "anomaly_score": score,
                "risk_flag": flag
            })

        self.db.commit()
        logger.info(f"Completed risk anomaly analysis for agent_sk={agent_sk}. Evaluated {len(results)} records.")
        return results
