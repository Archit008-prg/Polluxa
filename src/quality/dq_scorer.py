import json
from datetime import datetime, timezone
from typing import Dict, Any
from sqlalchemy.orm import Session
from src.database.models import DQCheckHistory
from config.logging_config import get_logger

logger = get_logger("dq_scorer")

def record_dq_check(db: Session, run_id: str, dq_metrics: Dict[str, Any], failure_details: str = None) -> DQCheckHistory:
    """Persists data quality run scores to dq_check_history for trending analysis."""
    check_entry = DQCheckHistory(
        run_id=run_id,
        check_timestamp=datetime.now(timezone.utc),
        completeness_score=dq_metrics["completeness"],
        uniqueness_score=dq_metrics["uniqueness"],
        validity_score=dq_metrics["validity"],
        timeliness_score=dq_metrics["timeliness"],
        referential_integrity_score=dq_metrics["referential_integrity"],
        composite_dq_score=dq_metrics["composite_score"],
        passed=dq_metrics["passed"],
        failure_details=failure_details
    )
    
    db.add(check_entry)
    db.commit()
    db.refresh(check_entry)
    logger.info(f"Persisted DQ check record check_id={check_entry.check_id} for run_id={run_id}")
    return check_entry
