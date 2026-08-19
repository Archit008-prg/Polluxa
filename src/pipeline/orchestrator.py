import json
import uuid
from datetime import datetime, date, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from config.settings import settings, ACCOUNT_AGE_RISK_MATRIX
from config.logging_config import get_logger
from src.database.connection import SessionLocal
from src.database.models import (
    DimAgent, DimLead, DimCampaign, DimDate, FactOutreachActivity,
    FactDailyAgentSummary, DeadLetterQueue, PipelineRun
)
from src.quality.validator import DataQualityValidator
from src.quality.dq_scorer import record_dq_check
from src.modeling.anomaly_detector import RiskAnomalyDetector
from src.modeling.capacity_optimizer import DailyCapacityOptimizer
from src.utils.alert_handler import AlertHandler

logger = get_logger("pipeline_orchestrator")

class IngestionPipelineOrchestrator:
    """
    End-to-End Ingestion Pipeline Orchestrator.
    Executes idempotent ingestion, incremental loading via watermarks, SCD Type 2 dimension mapping,
    5-point DQ checks, dead-letter routing, risk modeling, and capacity optimization.
    """

    def __init__(self, db_session: Optional[Session] = None):
        self.db = db_session or SessionLocal()
        self.should_close_session = db_session is None

    def close(self):
        if self.should_close_session and self.db:
            self.db.close()

    def get_last_watermark(self) -> Optional[datetime]:
        """Retrieves the last successful pipeline watermark."""
        last_run = (
            self.db.query(PipelineRun)
            .filter(PipelineRun.status.in_(["SUCCESS", "PARTIAL_SUCCESS"]))
            .order_by(PipelineRun.end_time.desc())
            .first()
        )
        return last_run.new_watermark if last_run else None

    def run_pipeline(
        self,
        raw_events: Optional[List[Dict[str, Any]]] = None,
        watermark_timestamp: Optional[datetime] = None,
        simulate_429: bool = False,
        simulate_malformed: bool = False
    ) -> PipelineRun:
        """Executes full pipeline run with error boundary and correlation logging."""
        run_id = f"RUN-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"
        start_time = datetime.now(timezone.utc)
        
        last_watermark = watermark_timestamp or self.get_last_watermark()
        
        pipeline_run = PipelineRun(
            run_id=run_id,
            start_time=start_time,
            status="IN_PROGRESS",
            watermark_used=last_watermark,
            rows_ingested=0,
            rows_failed=0
        )
        self.db.add(pipeline_run)
        self.db.commit()

        logger.info(f"Started pipeline run {run_id} (Watermark: {last_watermark})")

        try:
            # 1. Fetch data if not directly provided
            if raw_events is None:
                from src.api.client import PolluxaApiClient
                client = PolluxaApiClient()
                raw_events, new_watermark = client.fetch_outreach_events(
                    since_watermark=last_watermark,
                    simulate_429=simulate_429,
                    simulate_malformed=simulate_malformed
                )
            else:
                new_watermark = datetime.now(timezone.utc)

            # 2. Perform 5-Point Data Quality Audit
            validator = DataQualityValidator(self.db)
            valid_events, dead_letters, dq_metrics = validator.validate_batch(raw_events)

            # Record DQ Check Audit
            record_dq_check(self.db, run_id, dq_metrics)

            if not dq_metrics["passed"]:
                AlertHandler.send_alert(
                    alert_type="DQ_THRESHOLD_BREACH",
                    message=f"Composite Data Quality score ({dq_metrics['composite_score']}) fell below threshold ({settings.DQ_PASS_THRESHOLD})",
                    payload=dq_metrics
                )

            # 3. Route failed records to Dead Letter Queue (DLQ)
            for raw_evt, reason in dead_letters:
                dlq_entry = DeadLetterQueue(
                    run_id=run_id,
                    raw_payload=json.dumps(raw_evt),
                    failure_reason=reason
                )
                self.db.add(dlq_entry)
            self.db.commit()

            # 4. Ingest Clean Events with Idempotency & Dimension Registration
            ingested_count = 0
            agents_updated = set()

            for evt in valid_events:
                # Ensure Agent exists (SCD Type 2 lookup/creation)
                agent_id = evt["agent_id"]
                agent = self._get_or_create_agent(agent_id, evt.get("agent_name", f"Agent {agent_id}"))
                agents_updated.add(agent.agent_sk)

                # Ensure Lead exists
                lead = self._get_or_create_lead(evt)

                # Ensure Campaign exists
                campaign = self._get_or_create_campaign(evt)

                # Date Key resolution
                evt_ts = datetime.fromisoformat(evt["timestamp"].replace("Z", "+00:00"))
                date_key = int(evt_ts.strftime("%Y%m%d"))
                self._ensure_date_key_exists(date_key, evt_ts.date())

                # Idempotency Check: skip if event_id already exists in fact table
                existing = self.db.query(FactOutreachActivity.fact_id).filter_by(event_id=evt["event_id"]).first()
                if not existing:
                    fact = FactOutreachActivity(
                        event_id=evt["event_id"],
                        date_key=date_key,
                        agent_sk=agent.agent_sk,
                        lead_sk=lead.lead_sk,
                        campaign_sk=campaign.campaign_sk,
                        action_type=evt["action_type"],
                        timestamp=evt_ts,
                        response_time_seconds=evt.get("response_time_seconds")
                    )
                    self.db.add(fact)
                    ingested_count += 1

            self.db.commit()

            # 5. Build/Update Daily Summaries & Risk Modeling for impacted agents
            detector = RiskAnomalyDetector(self.db)
            optimizer = DailyCapacityOptimizer(self.db)

            for agent_sk in agents_updated:
                self._recalculate_daily_summaries_for_agent(agent_sk)
                detector.analyze_agent_performance(agent_sk)
                
                # Fetch latest summary to optimize capacity
                latest_sum = (
                    self.db.query(FactDailyAgentSummary)
                    .filter_by(agent_sk=agent_sk)
                    .order_by(FactDailyAgentSummary.date_key.desc())
                    .first()
                )
                if latest_sum:
                    optimizer.optimize_agent_capacity(agent_sk, latest_sum.summary_sk)

            # 6. Finalize Run Metadata
            end_time = datetime.now(timezone.utc)
            pipeline_run.end_time = end_time
            pipeline_run.status = "SUCCESS" if len(dead_letters) == 0 else "PARTIAL_SUCCESS"
            pipeline_run.rows_ingested = ingested_count
            pipeline_run.rows_failed = len(dead_letters)
            pipeline_run.new_watermark = new_watermark
            self.db.commit()

            logger.info(
                f"Pipeline Run {run_id} Completed successfully: "
                f"Ingested={ingested_count}, Failed={len(dead_letters)}, Status={pipeline_run.status}"
            )
            return pipeline_run

        except Exception as e:
            self.db.rollback()
            end_time = datetime.now(timezone.utc)
            pipeline_run.end_time = end_time
            pipeline_run.status = "FAILED"
            pipeline_run.error_summary = str(e)
            self.db.commit()
            
            AlertHandler.send_alert(
                alert_type="PIPELINE_FAILURE",
                message=f"Pipeline run {run_id} failed catastrophically: {e}",
                payload={"run_id": run_id}
            )
            logger.error(f"Pipeline Run {run_id} FAILED: {e}")
            raise e
        finally:
            self.close()

    def _get_or_create_agent(self, agent_id: str, name: str) -> DimAgent:
        """Retrieves or creates active DimAgent record with SCD Type 2 defaults."""
        agent = self.db.query(DimAgent).filter_by(agent_id=agent_id, is_current=True).first()
        if not agent:
            # Map tier defaults
            tier = "1+ Year"
            tier_info = ACCOUNT_AGE_RISK_MATRIX[tier]
            agent = DimAgent(
                agent_id=agent_id,
                agent_name=name,
                account_age_tier=tier,
                risk_classification=tier_info["risk_classification"],
                daily_invite_ceiling=tier_info["daily_invites"],
                daily_message_ceiling=tier_info["daily_messages"],
                status="Active",
                is_current=True
            )
            self.db.add(agent)
            self.db.commit()
            self.db.refresh(agent)
        return agent

    def _get_or_create_lead(self, evt: Dict[str, Any]) -> DimLead:
        """Retrieves or creates DimLead record."""
        lead_id = evt["lead_id"]
        lead = self.db.query(DimLead).filter_by(lead_id=lead_id).first()
        if not lead:
            lead = DimLead(
                lead_id=lead_id,
                lead_name=evt.get("lead_name", f"Lead {lead_id}"),
                company=evt.get("company", "Unknown"),
                industry=evt.get("industry", "Unknown"),
                target_segment=evt.get("target_segment", "General")
            )
            self.db.add(lead)
            self.db.commit()
            self.db.refresh(lead)
        return lead

    def _get_or_create_campaign(self, evt: Dict[str, Any]) -> DimCampaign:
        """Retrieves or creates DimCampaign record."""
        camp_id = evt["campaign_id"]
        campaign = self.db.query(DimCampaign).filter_by(campaign_id=camp_id).first()
        if not campaign:
            campaign = DimCampaign(
                campaign_id=camp_id,
                campaign_name=evt.get("campaign_name", f"Campaign {camp_id}"),
                target_segment=evt.get("target_segment", "General"),
                status="Active",
                launch_date=date.today()
            )
            self.db.add(campaign)
            self.db.commit()
            self.db.refresh(campaign)
        return campaign

    def _ensure_date_key_exists(self, date_key: int, dt: date):
        """Ensures dim_date contains the target date key."""
        exists = self.db.query(DimDate.date_key).filter_by(date_key=date_key).first()
        if not exists:
            dim_d = DimDate(
                date_key=date_key,
                full_date=dt,
                day_of_week=dt.strftime("%A"),
                month=dt.month,
                month_name=dt.strftime("%B"),
                quarter=(dt.month - 1) // 3 + 1,
                year=dt.year,
                is_weekend=dt.weekday() >= 5
            )
            self.db.add(dim_d)
            self.db.commit()

    def _recalculate_daily_summaries_for_agent(self, agent_sk: int):
        """Aggregates raw event activity into daily agent metrics."""
        agent = self.db.query(DimAgent).get(agent_sk)
        activities = self.db.query(FactOutreachActivity).filter_by(agent_sk=agent_sk).all()
        
        # Group by date_key
        daily_groups: Dict[int, Dict[str, int]] = {}
        for a in activities:
            dk = a.date_key
            if dk not in daily_groups:
                daily_groups[dk] = {"invite": 0, "accept": 0, "message": 0, "reply": 0}
            if a.action_type in daily_groups[dk]:
                daily_groups[dk][a.action_type] += 1

        for dk, counts in daily_groups.items():
            invites = counts["invite"]
            accepts = counts["accept"]
            msgs = counts["message"]
            replies = counts["reply"]

            acc_rate = round(accepts / (invites + 1e-5), 4) if invites > 0 else 0.0
            rep_rate = round(replies / (msgs + 1e-5), 4) if msgs > 0 else 0.0

            inv_util = round(invites / agent.daily_invite_ceiling, 4) if agent.daily_invite_ceiling > 0 else 0.0
            msg_util = round(msgs / agent.daily_message_ceiling, 4) if agent.daily_message_ceiling > 0 else 0.0

            summary = self.db.query(FactDailyAgentSummary).filter_by(agent_sk=agent_sk, date_key=dk).first()
            if not summary:
                summary = FactDailyAgentSummary(
                    agent_sk=agent_sk,
                    date_key=dk,
                    recommended_invite_capacity=agent.daily_invite_ceiling,
                    recommended_message_capacity=agent.daily_message_ceiling
                )
                self.db.add(summary)

            summary.invites_sent = invites
            summary.accepts_received = accepts
            summary.messages_sent = msgs
            summary.replies_received = replies
            summary.ghosted_count = max(0, invites - accepts)
            summary.acceptance_rate = acc_rate
            summary.reply_rate = rep_rate
            summary.invite_utilization_pct = inv_util
            summary.message_utilization_pct = msg_util

        self.db.commit()
