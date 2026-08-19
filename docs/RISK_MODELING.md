# Advanced Analytics & Risk Anomaly Modeling

## Executive Summary
LinkedIn algorithms actively monitor automation behavior for rapid spikes, uncharacteristic response delays, and collapsing acceptance rates to apply account restrictions or shadow-bans.

This risk modeling framework combines **Account Age Constraints (Part 1 Baseline)** with a **Statistical 7-Day Rolling Z-Score Anomaly Detector** to calculate real-time risk scores and dynamically throttle daily capacity limits before algorithmic penalties occur.

---

## 1. Statistical Basis & Methodology

The anomaly score combines three weighted risk indicators evaluated on a rolling 7-day window per agent:

$$\text{Anomaly Score} = 0.50 \cdot Z_{\text{Acceptance Collapse}} + 0.30 \cdot Z_{\text{Reply Decay}} + 0.20 \cdot R_{\text{Ghosting}}$$

### Components:
1. **Acceptance-Rate Collapse ($Z_{\text{Acceptance Collapse}}$)**:
   - Measures positive deviation when current acceptance rate drops below the rolling 7-day average:
     $$Z_{\text{Acceptance Collapse}} = \max\left(0, \frac{\mu_{7d} - \text{AcceptanceRate}_{\text{current}}}{\sigma_{7d} + \epsilon}\right)$$
   - *Rationale*: A sudden collapse in acceptance rate indicates algorithmic restriction or poor lead quality targeting.

2. **Reply Decay ($Z_{\text{Reply Decay}}$)**:
   - Measures downward trend in prospect replies:
     $$Z_{\text{Reply Decay}} = \max\left(0, \frac{\mu_{\text{reply}, 7d} - \text{ReplyRate}_{\text{current}}}{\sigma_{\text{reply}, 7d} + \epsilon}\right)$$

3. **Ghosting Ratio ($R_{\text{Ghosting}}$)**:
   - Proportion of sent connection invites that remain unanswered past expected SLA:
     $$R_{\text{Ghosting}} = \frac{\text{Invites Sent} - \text{Accepts Received}}{\text{Invites Sent} + \epsilon}$$

---

## 2. Risk Classification & Throttling Rules

| Anomaly Score Range | Risk Flag | Throttle Multiplier | Action Taken |
| :--- | :--- | :--- | :--- |
| **Score < 1.5** | `Normal` | **1.00 (100%)** | Full SOP Account Age limit permitted. |
| **1.5 ≤ Score < 2.5** | `Warning` | **0.70 (70%)** | 30% capacity reduction. Alert logged. |
| **Score ≥ 2.5** | `Critical` | **0.40 (40%)** | 60% capacity reduction. Shadow-ban prevention alert dispatched. |

---

## 3. Account Age Tier Ceilings (SOP Baseline)

Dynamic recommendations are strictly bounded by the Account Age ceilings declared during onboarding:

| Account Age Tier | Risk Classification | Max Daily Invites | Max Daily Messages |
| :--- | :--- | :--- | :--- |
| `< 1 Month` | Very High Risk | 5 | 10 |
| `1 Month` | High Risk | 10 | 15 |
| `2–6 Months` | Moderate Risk | 15 | 25 |
| `6–12 Months` | Low Risk | 25 | 40 |
| `1+ Year` | Minimal Risk | 30 | 60 |

---

## 4. Stated Assumptions & Limitations

1. **Cold Start Assumption**: New agents with < 3 days of historical data default to baseline tier limits until standard deviation can be computed.
2. **Weekend Seasonality**: Standard deviation smoothing accounts for weekend dips in corporate B2B LinkedIn activity.
3. **Model Limitations**: The model assumes lead quality is homogeneous within campaigns. Heterogeneous targeting may temporarily skew reply decay metrics.
