import time
import random
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, Header, HTTPException, Query, Response

app = FastAPI(title="Polluxa Enterprise API Mock", version="1.0.0")

# In-memory mock storage
MOCK_AGENTS = [
    {
        "agent_id": "AGT-001",
        "agent_name": "Sarah Connor (Tech Recruiter)",
        "account_age_tier": "1+ Year",
        "risk_classification": "Minimal Risk",
        "status": "Active"
    },
    {
        "agent_id": "AGT-002",
        "agent_name": "Alex Mercer (Executive Outreach)",
        "account_age_tier": "6–12 Months",
        "risk_classification": "Low Risk",
        "status": "Active"
    },
    {
        "agent_id": "AGT-003",
        "agent_name": "Jordan Lee (SaaS SDR Agent)",
        "account_age_tier": "1 Month",
        "risk_classification": "High Risk",
        "status": "Active"
    },
    {
        "agent_id": "AGT-004",
        "agent_name": "Taylor Swift (New Account Agent)",
        "account_age_tier": "< 1 Month",
        "risk_classification": "Very High Risk",
        "status": "Ghosted"
    }
]

MOCK_CAMPAIGNS = [
    {
        "campaign_id": "CMP-101",
        "campaign_name": "Q3 Senior Dev Recruitment",
        "target_segment": "Engineering Leads",
        "status": "Active",
        "launch_date": "2026-06-01"
    },
    {
        "campaign_id": "CMP-102",
        "campaign_name": "Enterprise VP Sales Outreach",
        "target_segment": "Sales Executives",
        "status": "Active",
        "launch_date": "2026-07-15"
    }
]

def verify_token(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized: Missing or invalid Bearer token")

@app.get("/api/v1/agents")
def get_agents(authorization: Optional[str] = Header(None)):
    verify_token(authorization)
    return {"status": "success", "data": MOCK_AGENTS}

@app.get("/api/v1/campaigns")
def get_campaigns(authorization: Optional[str] = Header(None)):
    verify_token(authorization)
    return {"status": "success", "data": MOCK_CAMPAIGNS}

@app.get("/api/v1/outreach/events")
def get_outreach_events(
    since: Optional[str] = Query(None),
    limit: int = Query(100),
    simulate_429: bool = Query(False),
    simulate_malformed: bool = Query(False),
    authorization: Optional[str] = Header(None)
):
    verify_token(authorization)
    
    if simulate_429:
        raise HTTPException(status_code=429, detail="Rate limit exceeded: Please back off.")
        
    now = datetime.now(timezone.utc)
    base_time = datetime.fromisoformat(since) if since else now - timedelta(days=7)
    
    events = []
    actions = ["invite", "accept", "message", "reply"]
    agents = MOCK_AGENTS
    
    for i in range(1, limit + 1):
        evt_time = base_time + timedelta(minutes=i * 5)
        agent = random.choice(agents)
        action = random.choice(actions)
        
        event = {
            "event_id": f"EVT-{int(evt_time.timestamp())}-{i}",
            "agent_id": agent["agent_id"],
            "lead_id": f"LEAD-{random.randint(1000, 9999)}",
            "lead_name": f"Lead Candidate {random.randint(1, 500)}",
            "company": random.choice(["Google", "Microsoft", "Meta", "Amazon", "Polluxa"]),
            "industry": "Software Engineering",
            "target_segment": "Engineering Leads",
            "campaign_id": "CMP-101",
            "action_type": action,
            "timestamp": evt_time.isoformat(),
            "response_time_seconds": random.randint(300, 86400) if action in ["accept", "reply"] else None
        }
        events.append(event)
        
    if simulate_malformed:
        events.append({
            "event_id": "EVT-MALFORMED-999",
            "agent_id": None, # Malformed missing agent_id
            "lead_id": "INVALID-LEAD",
            "action_type": "unknown_action",
            "timestamp": "invalid-timestamp-string"
        })
        
    return {
        "status": "success",
        "count": len(events),
        "watermark": now.isoformat(),
        "data": events
    }
