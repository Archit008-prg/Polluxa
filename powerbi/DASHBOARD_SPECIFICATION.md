# Power BI Dashboard Visual Specification & DAX Data Model Guide

## Overview
This document outlines the visual structure, layout, data model relationships, and DAX integration steps for building the production **LinkedIn Agent Analytics Platform Dashboard** in Power BI Desktop.

---

## 1. Data Model & Relationships (Star Schema)

Ensure the following 1-to-Many relationships are set up in Power BI:

| From Table (Dimension) | From Column | To Table (Fact) | To Column | Cardinality | Cross Filter Direction |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `dim_agent` | `agent_sk` | `fact_outreach_activity` | `agent_sk` | 1 to Many | Single |
| `dim_lead` | `lead_sk` | `fact_outreach_activity` | `lead_sk` | 1 to Many | Single |
| `dim_campaign` | `campaign_sk` | `fact_outreach_activity` | `campaign_sk` | 1 to Many | Single |
| `dim_date` | `date_key` | `fact_outreach_activity` | `date_key` | 1 to Many | Single |
| `dim_agent` | `agent_sk` | `fact_daily_agent_summary` | `agent_sk` | 1 to Many | Single |
| `dim_date` | `date_key` | `fact_daily_agent_summary` | `date_key` | 1 to Many | Single |

---

## 2. Page Breakdown & Visual Blueprint

### Page 1: Executive Overview & Core KPIs
- **Header KPI Cards**:
  - `Total Invites Sent`
  - `Overall Acceptance Rate` (%)
  - `Overall Reply Rate` (%)
  - `Overall Conversion Rate` (%)
  - `Average Response Time (Hours)`
- **Visual 1 (Clustered Column Chart)**: `Invites Sent` vs `Accepts Received` by `dim_date[month_name]`.
- **Visual 2 (Gauge Visual)**: `Overall Acceptance Rate` against 35% target threshold.
- **Visual 3 (Donut Chart)**: `Active Agent Count`, `Paused Agent Count`, `Ghosted Agent Count` breakdown.

### Page 2: Agent Account Health & Risk Intelligence
- **Header KPI Cards**:
  - `Average Anomaly Score`
  - `Critical Risk Agent Count`
  - `Warning Risk Agent Count`
  - `Latest Composite DQ Score`
- **Visual 1 (Scatter Plot)**: `Acceptance Rate` (Y-axis) vs `Anomaly Score` (X-axis) grouped by `dim_agent[agent_name]`.
- **Visual 2 (Matrix Table)**:
  - Rows: `agent_name`, `account_age_tier`, `risk_classification`
  - Columns: `invites_sent`, `acceptance_rate`, `anomaly_score`, `risk_flag`, `Recommended Daily Invite Limit`
  - Conditional Formatting: Red highlight on `Critical`, Orange on `Warning`.
- **Visual 3 (Line Chart)**: 7-day rolling `Anomaly Score` trend by Agent.

### Page 3: Campaign Performance & Target Segment ROI
- **Visual 1 (Bar Chart)**: `Campaign Conversion Rate` by `dim_campaign[campaign_name]`.
- **Visual 2 (Heatmap / Treemap)**: Outreach Volume & Acceptance Rate by `dim_lead[industry]` and `dim_lead[target_segment]`.
- **Visual 3 (Funnel Visual)**: Invites -> Accepts -> Messages -> Replies Conversion Pipeline.

---

## 3. Importing DAX Measures
1. Open Power BI Desktop.
2. Connect to the SQLite/PostgreSQL database using ODBC/Native Connector.
3. In Model view, create a measure table named `_Measures`.
4. Copy and paste the explicit DAX formulas from [DAX_MEASURES.dax](file:///d:/Project/powerbi/DAX_MEASURES.dax).
