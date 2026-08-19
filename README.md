# End-to-End LinkedIn Agent Analytics Platform

Production-ready analytics platform that ingests, models, analyzes, and visualizes automated LinkedIn outreach data for Polluxa enterprise agents.

---

## 🌟 Key Platform Features

- **Part 1 SOP Integration Baseline**: Complete step-by-step evidence guide ([PART1_EVIDENCE_GUIDE.md](file:///d:/Project/docs/PART1_EVIDENCE_GUIDE.md)) for onboarding and risk tier configuration.
- **Part 2 Secure & Idempotent API Ingestion Engine**:
  - Secure token handling with zero hardcoded credentials.
  - Watermark-based incremental extraction.
  - Exponential backoff with rate-limit awareness (HTTP 429) and dead-letter queue routing.
  - Execution run metadata persistence (`pipeline_runs`).
- **Part 3 Star Schema Data Architecture**:
  - Conformed Fact & Dimension tables (`dim_agent` SCD Type 2, `dim_lead`, `dim_campaign`, `dim_date`, `fact_outreach_activity`, `fact_daily_agent_summary`).
  - Full Data Dictionary ([DATA_DICTIONARY.md](file:///d:/Project/docs/DATA_DICTIONARY.md)) and Architecture Spec ([ARCHITECTURE.md](file:///d:/Project/docs/ARCHITECTURE.md)).
- **Part 4 Automated Data Quality & Governance**:
  - 5-point quality audit framework (Completeness, Uniqueness, Validity, Timeliness, Referential Integrity).
  - Composite DQ scoring (90.0% SLA threshold) with historical audit logging (`dq_check_history`).
  - Webhook/Console alert triggers on SLA breach.
- **Part 5 Advanced Analytics & Risk Anomaly Modeling**:
  - Statistical 7-day rolling Z-Score model to detect acceptance-rate collapse, reply decay, and ghosting patterns ([RISK_MODELING.md](file:///d:/Project/docs/RISK_MODELING.md)).
  - Risk-throttled daily capacity limits strictly constrained by Part 1 account age ceilings.
- **Part 6 Dual Visualizations & Analytics Layer**:
  - Production DAX measure library ([DAX_MEASURES.dax](file:///d:/Project/powerbi/DAX_MEASURES.dax)) and visual spec ([DASHBOARD_SPECIFICATION.md](file:///d:/Project/powerbi/DASHBOARD_SPECIFICATION.md)) for Power BI.
  - Interactive Web Analytics Dashboard in `web_dashboard/` (HTML5/Chart.js).
- **Part 7 DevOps, Containerization & CI/CD**:
  - Multi-stage `Dockerfile`, `docker-compose.yml`, structured JSON logger with correlation IDs.
  - GitHub Actions CI workflow ([.github/workflows/ci.yml](file:///d:/Project/.github/workflows/ci.yml)).
- **Part 8 Live Resilience Demonstration**:
  - Demonstration script (`scripts/demo_resilience.py`) proving idempotency, malformed input rejection, and end-to-end data pipeline refresh.

---

## 🚀 Quick Start Guide

### 1. Environment Setup
```bash
# Clone repository into workspace
cd d:\Project

# Create virtual environment (optional)
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Database Initialization
```bash
python scripts/init_db.py
```

### 3. Run Pipeline Orchestrator & Ingest Data
```bash
python scripts/run_pipeline.py
```

### 4. Run Live Resilience Demonstration CLI (Part 8)
```bash
python scripts/demo_resilience.py
```

### 5. Launch Interactive Web Analytics Dashboard (Part 6)
Open `d:\Project\web_dashboard\index.html` in your web browser, or launch via python web server:
```bash
python -m http.server 8080 --directory web_dashboard
```
Then navigate to `http://localhost:8080`.

---

## 🧪 Running Automated Tests

Run the full pytest suite:
```bash
pytest
```

---

## 🐳 Docker Deployment

Build and start system via Docker Compose:
```bash
docker-compose up --build
```
