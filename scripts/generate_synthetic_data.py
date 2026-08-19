import sys
import random
import uuid
from pathlib import Path
from datetime import datetime, timedelta, timezone

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.database.connection import SessionLocal, init_database
from src.database.models import DimAgent, DimLead, DimCampaign, DimDate
from config.settings import ACCOUNT_AGE_RISK_MATRIX
from config.logging_config import get_logger

logger = get_logger("synthetic_data_generator")

AGENTS_SEED = [
    {"id": "AGT-001", "name": "Sarah Connor (Tech Recruiter)", "tier": "1+ Year"},
    {"id": "AGT-002", "name": "Alex Mercer (Executive Outreach)", "tier": "6–12 Months"},
    {"id": "AGT-003", "name": "Jordan Lee (SaaS SDR)", "tier": "1 Month"},
    {"id": "AGT-004", "name": "Taylor Swift (New SDR)", "tier": "< 1 Month"}
]

CAMPAIGNS_SEED = [
    {"id": "CMP-101", "name": "Q3 Senior Dev Recruitment", "segment": "Engineering Leads"},
    {"id": "CMP-102", "name": "Enterprise VP Sales Outreach", "segment": "Sales Executives"}
]

def generate_synthetic_data(days: int = 14, include_bad_records: bool = True):
    """Seeds realistic multi-agent outreach event streams with anomaly patterns."""
    db = SessionLocal()
    init_database()
    
    logger.info("Seeding synthetic dimensions...")
    
    # 1. Seed Agents
    agent_map = {}
    for a_info in AGENTS_SEED:
        agent = db.query(DimAgent).filter_by(agent_id=a_info["id"], is_current=True).first()
        if not agent:
            tier_info = ACCOUNT_AGE_RISK_MATRIX[a_info["tier"]]
            agent = DimAgent(
                agent_id=a_info["id"],
                agent_name=a_info["name"],
                account_age_tier=a_info["tier"],
                risk_classification=tier_info["risk_classification"],
                daily_invite_ceiling=tier_info["daily_invites"],
                daily_message_ceiling=tier_info["daily_messages"],
                status="Active",
                is_current=True
            )
            db.add(agent)
            db.commit()
            db.refresh(agent)
        agent_map[a_info["id"]] = agent

    # 2. Seed Campaigns
    campaign_map = {}
    for c_info in CAMPAIGNS_SEED:
        camp = db.query(DimCampaign).filter_by(campaign_id=c_info["id"]).first()
        if not camp:
            camp = DimCampaign(
                campaign_id=c_info["id"],
                campaign_name=c_info["name"],
                target_segment=c_info["segment"],
                status="Active",
                launch_date=datetime.now(timezone.utc).date() - timedelta(days=30)
            )
            db.add(camp)
            db.commit()
            db.refresh(camp)
        campaign_map[c_info["id"]] = camp

    # 3. Generate Outreach Events over 14 Days
    events = []
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    
    actions = ["invite", "accept", "message", "reply"]

    logger.info(f"Generating synthetic events from {start_date.date()} to {end_date.date()}...")

    for day_offset in range(days):
        current_day = start_date + timedelta(days=day_offset)
        
        for agent_id, agent in agent_map.items():
            # Apply tier ceilings
            max_invites = agent.daily_invite_ceiling
            max_messages = agent.daily_message_ceiling

            # Inject simulated acceptance collapse for AGT-003 on recent days
            if agent_id == "AGT-003" and day_offset > 8:
                accept_prob = 0.05 # Collapse
            else:
                accept_prob = 0.40

            invites_sent = random.randint(max(1, max_invites - 5), max_invites)
            
            for i in range(invites_sent):
                evt_time = current_day + timedelta(hours=random.randint(8, 17), minutes=random.randint(0, 59))
                lead_id = f"LEAD-{random.randint(1000, 9999)}"
                
                # Invite Event
                events.append({
                    "event_id": f"EVT-INV-{agent_id}-{int(evt_time.timestamp())}-{i}",
                    "agent_id": agent_id,
                    "agent_name": agent.agent_name,
                    "lead_id": lead_id,
                    "lead_name": f"Candidate {lead_id}",
                    "company": random.choice(["Tech Corp", "Data Scale Inc", "Cloud Native"]),
                    "industry": "Software & IT",
                    "target_segment": "Engineering Leads",
                    "campaign_id": "CMP-101",
                    "action_type": "invite",
                    "timestamp": evt_time.isoformat(),
                    "response_time_seconds": None
                })

                # Simulated Acceptance
                if random.random() < accept_prob:
                    acc_time = evt_time + timedelta(hours=random.randint(1, 12))
                    events.append({
                        "event_id": f"EVT-ACC-{agent_id}-{int(acc_time.timestamp())}-{i}",
                        "agent_id": agent_id,
                        "agent_name": agent.agent_name,
                        "lead_id": lead_id,
                        "lead_name": f"Candidate {lead_id}",
                        "company": "Tech Corp",
                        "industry": "Software & IT",
                        "target_segment": "Engineering Leads",
                        "campaign_id": "CMP-101",
                        "action_type": "accept",
                        "timestamp": acc_time.isoformat(),
                        "response_time_seconds": random.randint(3600, 43200)
                    })

                    # Follow-up message & reply
                    if random.random() < 0.60:
                        msg_time = acc_time + timedelta(hours=random.randint(1, 4))
                        events.append({
                            "event_id": f"EVT-MSG-{agent_id}-{int(msg_time.timestamp())}-{i}",
                            "agent_id": agent_id,
                            "agent_name": agent.agent_name,
                            "lead_id": lead_id,
                            "lead_name": f"Candidate {lead_id}",
                            "company": "Tech Corp",
                            "industry": "Software & IT",
                            "target_segment": "Engineering Leads",
                            "campaign_id": "CMP-101",
                            "action_type": "message",
                            "timestamp": msg_time.isoformat(),
                            "response_time_seconds": None
                        })

                        if random.random() < 0.40:
                            rep_time = msg_time + timedelta(hours=random.randint(2, 24))
                            events.append({
                                "event_id": f"EVT-REP-{agent_id}-{int(rep_time.timestamp())}-{i}",
                                "agent_id": agent_id,
                                "agent_name": agent.agent_name,
                                "lead_id": lead_id,
                                "lead_name": f"Candidate {lead_id}",
                                "company": "Tech Corp",
                                "industry": "Software & IT",
                                "target_segment": "Engineering Leads",
                                "campaign_id": "CMP-101",
                                "action_type": "reply",
                                "timestamp": rep_time.isoformat(),
                                "response_time_seconds": random.randint(7200, 86400)
                            })

    if include_bad_records:
        # Deliberately malformed records for Part 4/8 testing
        events.append({
            "event_id": "EVT-MALFORMED-MISSING-AGENT",
            "agent_id": None, # Missing Agent ID
            "lead_id": "LEAD-9999",
            "campaign_id": "CMP-101",
            "action_type": "invite",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        events.append({
            "event_id": "EVT-MALFORMED-BAD-TIMESTAMP",
            "agent_id": "AGT-001",
            "lead_id": "LEAD-9998",
            "campaign_id": "CMP-101",
            "action_type": "invite",
            "timestamp": "NOT-A-VALID-DATE"
        })

    db.close()
    logger.info(f"Generated {len(events)} synthetic outreach events.")
    return events

if __name__ == "__main__":
    generate_synthetic_data()
