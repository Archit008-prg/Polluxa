from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Date, Text, ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class DimAgent(Base):
    """SCD Type 2 Dimension table for LinkedIn Agents."""
    __tablename__ = "dim_agent"

    agent_sk = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String(50), nullable=False, index=True)
    agent_name = Column(String(100), nullable=False)
    account_age_tier = Column(String(50), nullable=False)  # e.g., "< 1 Month", "1+ Year"
    risk_classification = Column(String(50), nullable=False) # e.g., "Minimal Risk"
    daily_invite_ceiling = Column(Integer, nullable=False)
    daily_message_ceiling = Column(Integer, nullable=False)
    status = Column(String(50), nullable=False, default="Active") # Active, Paused, Ghosted
    is_current = Column(Boolean, nullable=False, default=True)
    effective_start = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    effective_end = Column(DateTime, nullable=True)

    fact_activities = relationship("FactOutreachActivity", back_populates="agent")
    fact_summaries = relationship("FactDailyAgentSummary", back_populates="agent")


class DimLead(Base):
    """Dimension table for outreach targets/leads."""
    __tablename__ = "dim_lead"

    lead_sk = Column(Integer, primary_key=True, autoincrement=True)
    lead_id = Column(String(50), unique=True, nullable=False, index=True)
    lead_name = Column(String(100), nullable=False)
    lead_title = Column(String(100), nullable=True)
    company = Column(String(100), nullable=True)
    industry = Column(String(100), nullable=True)
    target_segment = Column(String(100), nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    fact_activities = relationship("FactOutreachActivity", back_populates="lead")


class DimCampaign(Base):
    """Dimension table for marketing & recruitment outreach campaigns."""
    __tablename__ = "dim_campaign"

    campaign_sk = Column(Integer, primary_key=True, autoincrement=True)
    campaign_id = Column(String(50), unique=True, nullable=False, index=True)
    campaign_name = Column(String(100), nullable=False)
    target_segment = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False, default="Active")
    launch_date = Column(Date, nullable=False)

    fact_activities = relationship("FactOutreachActivity", back_populates="campaign")


class DimDate(Base):
    """Calendar Date Dimension table."""
    __tablename__ = "dim_date"

    date_key = Column(Integer, primary_key=True) # e.g., 20260819
    full_date = Column(Date, nullable=False, unique=True)
    day_of_week = Column(String(20), nullable=False)
    month = Column(Integer, nullable=False)
    month_name = Column(String(20), nullable=False)
    quarter = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    is_weekend = Column(Boolean, nullable=False)


class FactOutreachActivity(Base):
    """Grain: One row per outreach event (invite, accept, message, reply)."""
    __tablename__ = "fact_outreach_activity"

    fact_id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(100), unique=True, nullable=False, index=True) # Natural key for idempotency
    date_key = Column(Integer, ForeignKey("dim_date.date_key"), nullable=False, index=True)
    agent_sk = Column(Integer, ForeignKey("dim_agent.agent_sk"), nullable=False, index=True)
    lead_sk = Column(Integer, ForeignKey("dim_lead.lead_sk"), nullable=False, index=True)
    campaign_sk = Column(Integer, ForeignKey("dim_campaign.campaign_sk"), nullable=False, index=True)
    
    action_type = Column(String(50), nullable=False) # invite, accept, message, reply
    timestamp = Column(DateTime, nullable=False, index=True)
    response_time_seconds = Column(Float, nullable=True)

    agent = relationship("DimAgent", back_populates="fact_activities")
    lead = relationship("DimLead", back_populates="fact_activities")
    campaign = relationship("DimCampaign", back_populates="fact_activities")


class FactDailyAgentSummary(Base):
    """Grain: One row per LinkedIn Agent per calendar date."""
    __tablename__ = "fact_daily_agent_summary"
    __table_args__ = (UniqueConstraint("agent_sk", "date_key", name="uix_agent_date"),)

    summary_sk = Column(Integer, primary_key=True, autoincrement=True)
    date_key = Column(Integer, ForeignKey("dim_date.date_key"), nullable=False, index=True)
    agent_sk = Column(Integer, ForeignKey("dim_agent.agent_sk"), nullable=False, index=True)
    
    invites_sent = Column(Integer, nullable=False, default=0)
    accepts_received = Column(Integer, nullable=False, default=0)
    messages_sent = Column(Integer, nullable=False, default=0)
    replies_received = Column(Integer, nullable=False, default=0)
    ghosted_count = Column(Integer, nullable=False, default=0)
    
    invite_utilization_pct = Column(Float, nullable=False, default=0.0)
    message_utilization_pct = Column(Float, nullable=False, default=0.0)
    acceptance_rate = Column(Float, nullable=False, default=0.0)
    reply_rate = Column(Float, nullable=False, default=0.0)
    
    anomaly_score = Column(Float, nullable=False, default=0.0)
    risk_flag = Column(String(50), nullable=False, default="Normal") # Normal, Warning, Critical
    recommended_invite_capacity = Column(Integer, nullable=False)
    recommended_message_capacity = Column(Integer, nullable=False)

    agent = relationship("DimAgent", back_populates="fact_summaries")


class DeadLetterQueue(Base):
    """Capture for unparseable, corrupted, or failed ingestion payloads."""
    __tablename__ = "dead_letter_queue"

    dlq_id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(100), nullable=False, index=True)
    raw_payload = Column(Text, nullable=False)
    failure_reason = Column(Text, nullable=False)
    retry_count = Column(Integer, nullable=False, default=0)
    ingested_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))


class PipelineRun(Base):
    """Run metadata for every pipeline execution."""
    __tablename__ = "pipeline_runs"

    run_id = Column(String(100), primary_key=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    status = Column(String(50), nullable=False) # SUCCESS, FAILED, PARTIAL
    rows_ingested = Column(Integer, nullable=False, default=0)
    rows_failed = Column(Integer, nullable=False, default=0)
    watermark_used = Column(DateTime, nullable=True)
    new_watermark = Column(DateTime, nullable=True)
    error_summary = Column(Text, nullable=True)


class DQCheckHistory(Base):
    """Historical data quality audit log."""
    __tablename__ = "dq_check_history"

    check_id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(100), nullable=False, index=True)
    check_timestamp = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    
    completeness_score = Column(Float, nullable=False)
    uniqueness_score = Column(Float, nullable=False)
    validity_score = Column(Float, nullable=False)
    timeliness_score = Column(Float, nullable=False)
    referential_integrity_score = Column(Float, nullable=False)
    composite_dq_score = Column(Float, nullable=False)
    
    passed = Column(Boolean, nullable=False)
    failure_details = Column(Text, nullable=True)
