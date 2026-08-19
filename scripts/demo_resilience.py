import sys
import uuid
from pathlib import Path
from datetime import datetime, timezone

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.database.connection import SessionLocal, init_database
from src.database.models import FactOutreachActivity, DeadLetterQueue, DQCheckHistory, FactDailyAgentSummary
from src.pipeline.orchestrator import IngestionPipelineOrchestrator
from scripts.generate_synthetic_data import generate_synthetic_data
from config.logging_config import get_logger

logger = get_logger("demo_resilience")

def print_banner(title: str):
    print("\n" + "=" * 80)
    print(f"  LIVE DEMONSTRATION SCENARIO: {title}")
    print("=" * 80)

def demo_scenario_1_idempotent_recovery():
    print_banner("1. MID-RUN FAILURE & IDEMPOTENT RECOVERY (NO DUPLICATES)")
    db = SessionLocal()
    
    # 1. Generate clean batch
    test_events = [
        {
            "event_id": "DEMO-EVT-IDEMPOTENT-001",
            "agent_id": "AGT-001",
            "agent_name": "Sarah Connor",
            "lead_id": "LEAD-DEMO-1",
            "company": "Polluxa Enterprise",
            "industry": "Analytics",
            "target_segment": "Engineering",
            "campaign_id": "CMP-101",
            "action_type": "invite",
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        {
            "event_id": "DEMO-EVT-IDEMPOTENT-002",
            "agent_id": "AGT-001",
            "agent_name": "Sarah Connor",
            "lead_id": "LEAD-DEMO-2",
            "company": "Polluxa Enterprise",
            "industry": "Analytics",
            "target_segment": "Engineering",
            "campaign_id": "CMP-101",
            "action_type": "accept",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    ]

    orchestrator = IngestionPipelineOrchestrator(db_session=db)
    
    print("Step 1: First Ingestion Execution...")
    run1 = orchestrator.run_pipeline(raw_events=test_events)
    print(f" -> Run 1 Completed. Status: {run1.status}, Rows Ingested: {run1.rows_ingested}")
    
    initial_count = db.query(FactOutreachActivity).filter(FactOutreachActivity.event_id.startswith("DEMO-EVT-IDEMPOTENT")).count()
    print(f" -> Rows in Fact Table after Run 1: {initial_count}")

    print("\nStep 2: Re-running exact same payload (Simulating recovery retry)...")
    orchestrator2 = IngestionPipelineOrchestrator(db_session=db)
    run2 = orchestrator2.run_pipeline(raw_events=test_events)
    print(f" -> Run 2 Completed. Status: {run2.status}, Rows Ingested: {run2.rows_ingested}")

    final_count = db.query(FactOutreachActivity).filter(FactOutreachActivity.event_id.startswith("DEMO-EVT-IDEMPOTENT")).count()
    print(f" -> Rows in Fact Table after Recovery Run 2: {final_count}")

    assert initial_count == final_count, "FAIL: Idempotency failed - Duplicate records inserted!"
    print("\n[SUCCESS] Idempotency Verified! Re-running pipeline produced 0 duplicate rows.")


def demo_scenario_2_malformed_input():
    print_banner("2. MALFORMED / BAD-QUALITY INPUT REJECTION & DEAD-LETTER QUEUE")
    db = SessionLocal()

    bad_events = [
        {
            "event_id": "DEMO-MALFORMED-001",
            "agent_id": None, # Missing required agent_id
            "lead_id": "LEAD-BAD",
            "campaign_id": "CMP-101",
            "action_type": "invite",
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        {
            "event_id": "DEMO-MALFORMED-002",
            "agent_id": "AGT-001",
            "lead_id": "LEAD-BAD2",
            "campaign_id": "CMP-101",
            "action_type": "invalid_action", # Invalid enum value
            "timestamp": "INVALID-TIMESTAMP"
        },
        {
            "event_id": f"DEMO-CLEAN-{uuid.uuid4().hex[:6]}",
            "agent_id": "AGT-001",
            "lead_id": "LEAD-GOOD3",
            "company": "Polluxa",
            "industry": "Tech",
            "target_segment": "Engineering",
            "campaign_id": "CMP-101",
            "action_type": "invite",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    ]

    orchestrator = IngestionPipelineOrchestrator(db_session=db)
    print("Ingesting batch with 2 malformed records and 1 clean record...")
    run = orchestrator.run_pipeline(raw_events=bad_events)

    print(f" -> Run Completed. Ingested: {run.rows_ingested}, Failed/Dead-Lettered: {run.rows_failed}")

    # Inspect Dead Letter Queue
    dlq_records = db.query(DeadLetterQueue).filter(DeadLetterQueue.run_id == run.run_id).all()
    print(f" -> Captured {len(dlq_records)} entries in Dead Letter Queue:")
    for dlq in dlq_records:
        print(f"    - DLQ #{dlq.dlq_id}: Reason: {dlq.failure_reason}")

    # Inspect Data Quality Audit History
    latest_dq = db.query(DQCheckHistory).filter_by(run_id=run.run_id).first()
    if latest_dq:
        print(f" -> Composite DQ Audit Score: {latest_dq.composite_dq_score * 100:.1f}% (Passed: {latest_dq.passed})")

    assert len(dlq_records) == 2, "FAIL: Malformed records were not caught in Dead Letter Queue!"
    assert run.rows_ingested == 1, "FAIL: Clean record was not ingested!"
    print("\n[SUCCESS] Malformed data successfully rejected & routed to DLQ without pipeline crash.")


def demo_scenario_3_end_to_end_refresh():
    print_banner("3. END-TO-END REFRESH & STATISTICAL RISK ANOMALY MODELING")
    db = SessionLocal()

    print("Generating full synthetic 7-day dataset with simulated acceptance collapse...")
    events = generate_synthetic_data(days=7, include_bad_records=False)

    orchestrator = IngestionPipelineOrchestrator(db_session=db)
    run = orchestrator.run_pipeline(raw_events=events)

    print(f" -> Ingestion Complete. Processed {run.rows_ingested} records into Star Schema database.")

    # Inspect Risk Modeling Results
    summaries = db.query(FactDailyAgentSummary).all()
    print(f" -> Evaluated {len(summaries)} daily agent summary records:")
    
    for s in summaries[:5]:
        print(
            f"    - Agent SK {s.agent_sk} | Date: {s.date_key} | Invites: {s.invites_sent} | "
            f"Acc Rate: {s.acceptance_rate * 100:.1f}% | Anomaly Score: {s.anomaly_score} | "
            f"Risk Flag: {s.risk_flag} | Rec Limit: {s.recommended_invite_capacity}/day"
        )

    print("\n[SUCCESS] End-to-end pipeline refresh flow completed with updated risk intelligence!")

def main():
    print("\n" + "*" * 80)
    print(" POLLUXA LINKEDIN AGENT ANALYTICS PLATFORM - LIVE RESILIENCE DEMONSTRATION ")
    print("*" * 80)
    
    init_database()
    demo_scenario_1_idempotent_recovery()
    demo_scenario_2_malformed_input()
    demo_scenario_3_end_to_end_refresh()

    print("\n" + "*" * 80)
    print(" ALL DEMONSTRATION SCENARIOS PASSED WITH 100% SUCCESS ")
    print("*" * 80 + "\n")

if __name__ == "__main__":
    main()
