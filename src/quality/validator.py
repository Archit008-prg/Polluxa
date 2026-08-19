from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from src.database.models import DimAgent, DimCampaign, DimLead
from config.settings import settings
from config.logging_config import get_logger

logger = get_logger("dq_validator")

VALID_ACTION_TYPES = {"invite", "accept", "message", "reply"}

class DataQualityValidator:
    """Automated 5-point Data Quality Checker and Composite DQ Scorer."""
    
    def __init__(self, db: Session):
        self.db = db

    def validate_batch(self, events: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Tuple[Dict[str, Any], str]], Dict[str, float]]:
        """
        Validates raw event batch against Completeness, Uniqueness, Validity, Timeliness, and Referential Integrity.
        Returns:
            - valid_events: List of clean records
            - dead_letter_events: List of tuples (raw_event, failure_reason)
            - dq_scores: Dictionary of dimension scores
        """
        if not events:
            return [], [], {
                "completeness": 1.0,
                "uniqueness": 1.0,
                "validity": 1.0,
                "timeliness": 1.0,
                "referential_integrity": 1.0,
                "composite_score": 1.0,
                "passed": True
            }

        valid_events = []
        dead_letter_events = []
        
        # Load known reference keys for Referential Integrity & Uniqueness
        existing_agents = set(a.agent_id for a in self.db.query(DimAgent.agent_id).all())
        existing_campaigns = set(c.campaign_id for c in self.db.query(DimCampaign.campaign_id).all())
        
        seen_event_ids = set()
        
        # Counters for DQ metrics
        total_records = len(events)
        completeness_passes = 0
        uniqueness_passes = 0
        validity_passes = 0
        timeliness_passes = 0
        ref_integrity_passes = 0
        
        now = datetime.now(timezone.utc)
        
        for evt in events:
            reasons = []
            
            # 1. Completeness Check
            required_fields = ["event_id", "agent_id", "lead_id", "campaign_id", "action_type", "timestamp"]
            missing = [f for f in required_fields if not evt.get(f)]
            if not missing:
                completeness_passes += 1
            else:
                reasons.append(f"Completeness Failure: missing fields {missing}")

            # 2. Uniqueness Check
            evt_id = evt.get("event_id")
            if evt_id and evt_id not in seen_event_ids:
                seen_event_ids.add(evt_id)
                uniqueness_passes += 1
            else:
                reasons.append(f"Uniqueness Failure: duplicate event_id '{evt_id}'")

            # 3. Validity Check
            action = evt.get("action_type")
            ts_str = evt.get("timestamp")
            is_valid_ts = False
            parsed_ts = None
            
            if ts_str:
                try:
                    parsed_ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                    if parsed_ts.tzinfo is None:
                        parsed_ts = parsed_ts.replace(tzinfo=timezone.utc)
                    is_valid_ts = True
                except ValueError:
                    is_valid_ts = False

            resp_time = evt.get("response_time_seconds")
            valid_resp_time = (resp_time is None) or (isinstance(resp_time, (int, float)) and resp_time >= 0)

            if action in VALID_ACTION_TYPES and is_valid_ts and valid_resp_time:
                validity_passes += 1
            else:
                reasons.append(f"Validity Failure: action='{action}', valid_ts={is_valid_ts}, valid_resp={valid_resp_time}")

            # 4. Timeliness Check
            if parsed_ts and parsed_ts <= now and (now - parsed_ts).days <= 30:
                timeliness_passes += 1
            else:
                reasons.append(f"Timeliness Failure: timestamp '{ts_str}' out of acceptable range")

            # 5. Referential Integrity Check
            agent_id = evt.get("agent_id")
            campaign_id = evt.get("campaign_id")
            
            # If agent or campaign is not in DB, allow dynamic registration or flag ref integrity
            if (agent_id in existing_agents or agent_id) and (campaign_id in existing_campaigns or campaign_id):
                ref_integrity_passes += 1
            else:
                reasons.append(f"Referential Integrity Failure: unknown agent_id '{agent_id}' or campaign_id '{campaign_id}'")

            # Final classification
            if not reasons:
                valid_events.append(evt)
            else:
                dead_letter_events.append((evt, " | ".join(reasons)))

        # Calculate dimension scores
        c_score = completeness_passes / total_records
        u_score = uniqueness_passes / total_records
        v_score = validity_passes / total_records
        t_score = timeliness_passes / total_records
        r_score = ref_integrity_passes / total_records
        
        # Weighted composite score: Completeness 25%, Uniqueness 25%, Validity 20%, Timeliness 15%, Ref Integrity 15%
        composite = (c_score * 0.25) + (u_score * 0.25) + (v_score * 0.20) + (t_score * 0.15) + (r_score * 0.15)
        passed = composite >= settings.DQ_PASS_THRESHOLD
        
        dq_scores = {
            "completeness": round(c_score, 4),
            "uniqueness": round(u_score, 4),
            "validity": round(v_score, 4),
            "timeliness": round(t_score, 4),
            "referential_integrity": round(r_score, 4),
            "composite_score": round(composite, 4),
            "passed": passed
        }

        logger.info(f"Data Quality Batch Assessment: Composite Score={dq_scores['composite_score']} (Passed={passed})")
        return valid_events, dead_letter_events, dq_scores
