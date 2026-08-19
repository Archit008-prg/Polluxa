# Data Dictionary - Star Schema & System Tables

## 1. Dimension Tables

### `dim_agent` (Slowly Changing Dimension Type 2)
Grain: One row per agent profile version.

| Column Name | Data Type | Nullable | Primary/Foreign Key | Business Definition |
| :--- | :--- | :--- | :--- | :--- |
| `agent_sk` | INTEGER | No | PK | Surrogate key for agent record version. |
| `agent_id` | VARCHAR(50) | No | Natural Key | Unique identifier assigned by Polluxa. |
| `agent_name` | VARCHAR(100) | No | None | Display name of the LinkedIn agent. |
| `account_age_tier` | VARCHAR(50) | No | None | Declared profile age (< 1 Month, 1 Month, 2–6 Months, 6–12 Months, 1+ Year). |
| `risk_classification` | VARCHAR(50) | No | None | Baseline risk (Very High, High, Moderate, Low, Minimal). |
| `daily_invite_ceiling` | INTEGER | No | None | Maximum daily invite limit allowed by SOP matrix. |
| `daily_message_ceiling`| INTEGER | No | None | Maximum daily message limit allowed by SOP matrix. |
| `status` | VARCHAR(50) | No | None | Operational status (Active, Paused, Ghosted). |
| `is_current` | BOOLEAN | No | None | True if this is the active current version. |
| `effective_start` | DATETIME | No | None | Timestamp when this profile version became active. |
| `effective_end` | DATETIME | Yes | None | Timestamp when this profile version expired. |

---

### `dim_lead`
Grain: One row per target lead/candidate.

| Column Name | Data Type | Nullable | Primary/Foreign Key | Business Definition |
| :--- | :--- | :--- | :--- | :--- |
| `lead_sk` | INTEGER | No | PK | Surrogate key for lead. |
| `lead_id` | VARCHAR(50) | No | Natural Key | Unique lead ID. |
| `lead_name` | VARCHAR(100) | No | None | Full name of the candidate/prospect. |
| `lead_title` | VARCHAR(100) | Yes | None | Job title of lead. |
| `company` | VARCHAR(100) | Yes | None | Company organization. |
| `industry` | VARCHAR(100) | Yes | None | Industry category. |
| `target_segment` | VARCHAR(100) | Yes | None | Target audience segment (e.g. Engineering Leads). |

---

### `dim_campaign`
Grain: One row per outreach campaign.

| Column Name | Data Type | Nullable | Primary/Foreign Key | Business Definition |
| :--- | :--- | :--- | :--- | :--- |
| `campaign_sk` | INTEGER | No | PK | Surrogate key for campaign. |
| `campaign_id` | VARCHAR(50) | No | Natural Key | Unique campaign ID. |
| `campaign_name` | VARCHAR(100) | No | None | Display campaign name. |
| `target_segment` | VARCHAR(100) | No | None | Segment targeted by campaign. |
| `status` | VARCHAR(50) | No | None | Status (Active, Completed, Paused). |
| `launch_date` | DATE | No | None | Date campaign launched. |

---

### `dim_date`
Grain: One row per calendar date.

| Column Name | Data Type | Nullable | Primary/Foreign Key | Business Definition |
| :--- | :--- | :--- | :--- | :--- |
| `date_key` | INTEGER | No | PK | Integer representation YYYYMMDD. |
| `full_date` | DATE | No | None | Calendar date. |
| `day_of_week` | VARCHAR(20) | No | None | Day name (Monday - Sunday). |
| `month` | INTEGER | No | None | Month number (1 - 12). |
| `quarter` | INTEGER | No | None | Quarter (1 - 4). |
| `year` | INTEGER | No | None | Calendar year. |
| `is_weekend` | BOOLEAN | No | None | True if Saturday or Sunday. |

---

## 2. Fact Tables

### `fact_outreach_activity`
Grain: One row per individual outreach action (invite, accept, message, reply).

| Column Name | Data Type | Nullable | Primary/Foreign Key | Business Definition |
| :--- | :--- | :--- | :--- | :--- |
| `fact_id` | INTEGER | No | PK | Primary key event index. |
| `event_id` | VARCHAR(100) | No | Unique Key | Idempotency natural key. |
| `date_key` | INTEGER | No | FK -> `dim_date` | Event date key. |
| `agent_sk` | INTEGER | No | FK -> `dim_agent` | Agent surrogate key. |
| `lead_sk` | INTEGER | No | FK -> `dim_lead` | Lead surrogate key. |
| `campaign_sk` | INTEGER | No | FK -> `dim_campaign` | Campaign surrogate key. |
| `action_type` | VARCHAR(50) | No | None | Action type (invite, accept, message, reply). |
| `timestamp` | DATETIME | No | None | UTC event timestamp. |
| `response_time_seconds`| FLOAT | Yes | None | Latency between prompt and response. |

---

### `fact_daily_agent_summary`
Grain: One row per agent per calendar day.

| Column Name | Data Type | Nullable | Primary/Foreign Key | Business Definition |
| :--- | :--- | :--- | :--- | :--- |
| `summary_sk` | INTEGER | No | PK | Primary key summary index. |
| `date_key` | INTEGER | No | FK -> `dim_date` | Calendar date key. |
| `agent_sk` | INTEGER | No | FK -> `dim_agent` | Agent surrogate key. |
| `invites_sent` | INTEGER | No | None | Total invites sent on date. |
| `accepts_received` | INTEGER | No | None | Total connection accepts received. |
| `messages_sent` | INTEGER | No | None | Total messages sent on date. |
| `replies_received` | INTEGER | No | None | Total prospect replies received. |
| `ghosted_count` | INTEGER | No | None | Unresponsive invites (invites - accepts). |
| `acceptance_rate` | FLOAT | No | None | Ratio of accepts / invites. |
| `reply_rate` | FLOAT | No | None | Ratio of replies / messages. |
| `anomaly_score` | FLOAT | No | None | Statistical risk anomaly score. |
| `risk_flag` | VARCHAR(50) | No | None | Risk status (Normal, Warning, Critical). |
| `recommended_invite_capacity` | INTEGER | No | None | Risk-adjusted daily invite limit. |
| `recommended_message_capacity` | INTEGER | No | None | Risk-adjusted daily message limit. |
