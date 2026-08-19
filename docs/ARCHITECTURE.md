# End-to-End Architecture & Data Flow Specification

## System Architecture Diagram

```mermaid
flowchart TD
    subgraph External System
        PolluxaAPI["Polluxa Enterprise Portal API (sales.polluxa.com)"]
    end

    subgraph API Engineering & Ingestion Layer
        APIClient["PolluxaApiClient (Retries, Backoff, Watermarks)"]
        DLQ["Dead Letter Queue (dead_letter_queue)"]
    end

    subgraph Data Quality & Governance Engine
        DQValidator["Data Quality Validator (5-Point Audit)"]
        DQHistory["DQ History Logger (dq_check_history)"]
        Alerting["Alert Handler (Webhook & Log Notifications)"]
    end

    subgraph Star Schema Presentation Layer
        DimAgent["DimAgent (SCD Type 2)"]
        DimLead["DimLead"]
        DimCampaign["DimCampaign"]
        DimDate["DimDate"]
        FactActivity["FactOutreachActivity (Event Granularity)"]
        FactSummary["FactDailyAgentSummary (Daily Granularity)"]
    end

    subgraph Statistical Risk Modeling Engine
        AnomalyModel["Risk Anomaly Detector (7-Day Rolling Z-Score)"]
        CapacityOpt["Daily Capacity Optimizer (Tier Constrained)"]
    end

    subgraph Presentation & Visualization Layer
        PowerBI["Power BI Dashboard (Explicit DAX Measures)"]
        WebDashboard["Interactive Web Analytics Dashboard (HTML5/Chart.js)"]
    end

    PolluxaAPI --> APIClient
    APIClient --> DQValidator
    
    DQValidator -- Bad Records --> DLQ
    DQValidator -- Audit Scores --> DQHistory
    DQValidator -- SLA Breach --> Alerting

    DQValidator -- Clean Batch --> FactActivity
    FactActivity --> DimAgent
    FactActivity --> DimLead
    FactActivity --> DimCampaign
    FactActivity --> DimDate

    FactActivity --> FactSummary
    FactSummary --> AnomalyModel
    AnomalyModel --> CapacityOpt
    CapacityOpt --> FactSummary

    FactSummary --> PowerBI
    FactSummary --> WebDashboard
```

---

## Key Ingestion & Modeling Stages

1. **Incremental Watermarked Extraction**:
   - `PolluxaApiClient` queries `/outreach/events?since={watermark}`.
   - Watermarks track the latest successful timestamp, ensuring zero redundant data fetches.
2. **5-Point Data Quality Audit**:
   - Every batch is checked across Completeness, Uniqueness, Validity, Timeliness, and Referential Integrity.
   - Weighted composite score computed: Pass threshold = 90%.
   - Failed payloads routed to `dead_letter_queue`.
3. **Idempotent Ingestion into Star Schema**:
   - `FactOutreachActivity` enforces natural key uniqueness (`event_id`). Re-runs skip existing keys.
   - `DimAgent` uses Slow Changing Dimension (SCD Type 2) tracking tier and status transitions.
4. **Statistical Risk Anomaly Detection**:
   - Evaluates 7-day rolling window Z-scores on acceptance rates and reply rates.
   - Identifies acceptance-rate collapse, reply decay, and ghosting spikes.
5. **Dynamic Capacity Optimization**:
   - Calculates recommended daily invite and message ceilings per agent, respecting Part 1 Account Age tier limits (<1M, 1M, 2-6M, 6-12M, 1+Yr).
