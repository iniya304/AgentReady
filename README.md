# AgentReady

<p align="center">

# Predictive AI Revenue Recovery System

### Find revenue at risk. Predict the best recovery path. Govern every action.

**Built for the Razorpay AI Buildathon 2026 — AI Revenue Recovery Track**

</p>

---

## Table of Contents

- [Overview](#overview)
- [The Problem](#the-problem)
- [The Core Insight](#the-core-insight)
- [The Solution](#the-solution)
- [Why AgentReady Is Different](#why-agentready-is-different)
- [End-to-End Workflow](#end-to-end-workflow)
- [System Architecture](#system-architecture)
- [How the AI Decision Engine Works](#how-the-ai-decision-engine-works)
- [Recovery Probability](#recovery-probability)
- [Intervention Optimization](#intervention-optimization)
- [Expected Recovery Value](#expected-recovery-value)
- [Policy Engine and Guardrails](#policy-engine-and-guardrails)
- [Bounded Recovery Workflow](#bounded-recovery-workflow)
- [Idempotency and Duplicate Prevention](#idempotency-and-duplicate-prevention)
- [Human-in-the-Loop](#human-in-the-loop)
- [Recovery Copilot](#recovery-copilot)
- [Razorpay Integration](#razorpay-integration)
- [Database Architecture](#database-architecture)
- [Audit Trail](#audit-trail)
- [Machine Learning Model](#machine-learning-model)
- [Model Evaluation](#model-evaluation)
- [Model Comparison](#model-comparison)
- [Probability Calibration](#probability-calibration)
- [Batch Recovery Analysis](#batch-recovery-analysis)
- [API Reference](#api-reference)
- [Frontend](#frontend)
- [Backend](#backend)
- [Project Structure](#project-structure)
- [Technology Stack](#technology-stack)
- [Deployment](#deployment)
- [Environment Variables](#environment-variables)
- [Local Setup](#local-setup)
- [Testing](#testing)
- [Security and Safety](#security-and-safety)
- [Demo Walkthrough](#demo-walkthrough)
- [Current Demo Results](#current-demo-results)
- [Limitations](#limitations)
- [Future Roadmap](#future-roadmap)
- [Why This Fits the AI Revenue Recovery Track](#why-this-fits-the-ai-revenue-recovery-track)
- [Conclusion](#conclusion)

---

# Overview

**AgentReady** is a predictive AI revenue recovery system designed to help merchants decide how to recover revenue from failed payments.

Traditional payment recovery systems often use simple rules such as:

```text
Payment failed
      ↓
Retry
      ↓
Retry again
      ↓
Retry again
```

AgentReady approaches the problem differently.

It combines:

```text
Payment Data
     +
Customer Recovery History
     +
Failure Context
     +
Time Since Failure
     +
Machine Learning
     +
Intervention Optimization
     +
Expected Recovery Value
     +
Policy Guardrails
     +
Bounded Workflows
     +
Auditability
```

to answer:

> **Which failed payments should be prioritized, what intervention should be attempted, how valuable is the opportunity, and when should the system stop?**

The system is designed around a simple principle:

> **Prediction should inform action, but prediction alone should never authorize action.**

AgentReady therefore separates:

```text
WHAT IS LIKELY TO WORK?
```

from:

```text
WHAT IS THE SYSTEM ALLOWED TO DO?
```

---

# The Problem

Payment failures represent potential lost revenue.

A failed transaction can occur because of:

- Insufficient funds
- Card declines
- Expired cards
- Temporary network failures
- Other payment-processing failures

However, not every failed payment deserves the same recovery strategy.

Consider two failed payments:

```text
Payment A
Amount: ₹500
Recovery probability: 95%

Payment B
Amount: ₹15,000
Recovery probability: 20%
```

A system that only sorts by amount would prioritize Payment B.

A system that only sorts by probability would prioritize Payment A.

A merchant actually needs to understand the **expected value of recovery**.

AgentReady therefore evaluates both:

```text
Probability
     +
Economic Value
     +
Intervention
     +
Policy Constraints
```

---

# The Core Insight

The key insight behind AgentReady is:

> **Revenue recovery should be treated as a decision optimization problem rather than a simple payment retry problem.**

For every failed payment, there are multiple possible interventions.

For example:

```text
retry_now
retry_later
request_alternative_payment
request_card_update
```

The best intervention can vary based on:

- Failure reason
- Payment method
- Payment amount
- Customer history
- Previous attempts
- Recovery history
- Time since failure
- Intervention being considered

AgentReady evaluates these candidate interventions and estimates which one provides the highest expected recovery opportunity.

---

# The Solution

AgentReady follows the pipeline:

```text
              FAILED PAYMENT
                     |
                     v
          Payment + Customer Context
                     |
                     v
             ML Recovery Model
                     |
                     v
           Recovery Probability
                     |
                     v
          Evaluate Interventions
                     |
                     v
        Expected Recovery Value
                     |
                     v
              Policy Engine
                     |
          +----------+----------+
          |                     |
          v                     v
     AUTO EXECUTE         HUMAN REVIEW
          |                     |
          +----------+----------+
                     |
                     v
          Bounded Recovery Workflow
                     |
                     v
              Observe Outcome
                     |
              +------+------+
              |             |
           Success         Failed
              |             |
              v             v
             STOP       Next Attempt
                            |
                            v
                       Stop Rules
                            |
                            v
                       Audit Trail
```

---

# Why AgentReady Is Different

## 1. Predictive instead of purely reactive

A traditional recovery system might use:

```text
if payment_failed:
    retry()
```

AgentReady instead asks:

```text
What is the probability of recovery?
Which intervention should be used?
What is the expected recovery value?
Is automatic execution allowed?
Should a human review this case?
```

---

## 2. Multiple interventions are evaluated

AgentReady does not assume that every payment should use the same recovery strategy.

Candidate interventions include:

| Intervention | Typical Use |
|---|---|
| `retry_now` | Immediate retry for suitable failures |
| `retry_later` | Delay retry for failures such as insufficient funds |
| `request_alternative_payment` | Request another payment method |
| `request_card_update` | Ask customer to update an expired/invalid card |

The ML model evaluates the payment context together with each candidate intervention.

---

## 3. Expected-value prioritization

The system does not simply rank payments by:

```text
highest amount
```

or:

```text
highest probability
```

Instead it calculates:

```text
Expected Recovery Value
=
Payment Amount
×
Model-estimated Recovery Probability
```

This creates a more useful prioritization signal.

---

## 4. Policy-governed actions

Even if an opportunity has high expected value, the system can refuse automatic execution.

For example:

```text
High Expected Recovery Value
            +
Low Recovery Probability
            =
Human Review
```

This prevents financial actions from being directly controlled by an ML prediction.

---

## 5. Bounded workflows

AgentReady does not retry indefinitely.

A recovery workflow has explicit stopping conditions.

```text
Attempt 1
    ↓
Outcome
    ↓
Attempt 2
    ↓
Outcome
    ↓
STOP / HUMAN REVIEW
```

The current workflow is bounded to a maximum of **2 recovery attempts**.

---

## 6. Idempotent behavior

Repeated requests should not create uncontrolled duplicate actions.

AgentReady prevents:

- Duplicate recovery recommendations
- Duplicate pending workflow attempts

Existing recommendations can be reused rather than creating another action.

---

## 7. Auditable decisions

The system records important decision and workflow events.

Examples include:

```text
ML Recovery Prediction
Payment Analysis
Recovery Recommendation Reused
Recovery Workflow Decision
Recovery Attempt Created
Recovery Execution Blocked
Batch Recovery Analysis
```

This creates an operational trail for every important stage.

---

# End-to-End Workflow

## Step 1 — Detect failed payment

The backend retrieves failed payments from Supabase.

Example:

```text
Customer: cust_001
Amount: ₹2,499
Failure: insufficient_funds
Method: UPI
Status: failed
```

---

## Step 2 — Build recovery context

AgentReady combines payment data with customer recovery history.

The context can include:

```text
Payment amount
Payment method
Failure reason
Customer success rate
Customer tenure
Historical payment count
Historical failed payment count
Historical recovery count
Historical recovery rate
Previous attempts
Previous recovery attempts
Previous recovery success
Time since failure
Candidate intervention
```

---

## Step 3 — Generate ML probability

The recovery model generates a probability for the candidate intervention.

Example:

```text
Intervention:
retry_later

Recovery Probability:
83.56%
```

---

## Step 4 — Evaluate candidate interventions

AgentReady evaluates:

```text
retry_now
retry_later
request_alternative_payment
request_card_update
```

Each candidate receives:

```text
Recovery Probability
Expected Recovery Value
```

---

## Step 5 — Select the highest-value intervention

The candidates are ranked by Expected Recovery Value.

The highest-value candidate becomes the recommended intervention.

---

## Step 6 — Apply policy

The policy engine evaluates:

```text
Payment Amount
Recovery Probability
Previous Attempts
Previous Recovery Attempts
```

The final decision becomes:

```text
AUTO_EXECUTE
```

or:

```text
HUMAN_REVIEW
```

---

## Step 7 — Execute or escalate

If the action is permitted, the recovery workflow can proceed.

If not, AgentReady routes the payment to human review.

---

## Step 8 — Track outcome

Recovery attempts are persisted with:

```text
Attempt Number
Intervention
Status
Failure Reason
Created Time
Completion Time
Recovery Action
```

---

## Step 9 — Stop or continue

The workflow evaluates the outcome.

```text
Success
   ↓
STOP

Failure
   ↓
Next bounded attempt

Maximum attempts reached
   ↓
HUMAN REVIEW
```

---

# System Architecture

```text
                         ┌──────────────────────────┐
                         │      Next.js Frontend    │
                         │                          │
                         │ Recovery Command Center  │
                         │ Recovery Copilot         │
                         │ Payment Monitoring       │
                         │ Model Validation         │
                         │ Audit Trail              │
                         └────────────┬─────────────┘
                                      │
                                      │ REST API
                                      ↓
                         ┌──────────────────────────┐
                         │      FastAPI Backend     │
                         │                          │
                         │ AgentReady API           │
                         │ Recovery Intelligence    │
                         │ Workflow Engine          │
                         └────────────┬─────────────┘
                                      │
             ┌────────────────────────┼─────────────────────────┐
             │                        │                         │
             ↓                        ↓                         ↓
   ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
   │ Recovery Context │    │   ML Predictor    │    │  Policy Engine   │
   │                  │    │                  │    │                  │
   │ Payment Data     │    │ 38 Features      │    │ Amount Limits    │
   │ Customer History │    │ Recovery Prob.   │    │ Probability      │
   │ Timing           │    │                  │    │ Attempt Limits   │
   └────────┬─────────┘    └────────┬─────────┘    └────────┬─────────┘
            │                       │                       │
            └───────────────────────┼───────────────────────┘
                                    ↓
                         ┌──────────────────────────┐
                         │ Intervention Optimizer  │
                         │                          │
                         │ Candidate Evaluation     │
                         │ Expected Recovery Value  │
                         └────────────┬─────────────┘
                                      ↓
                         ┌──────────────────────────┐
                         │ Bounded Recovery Workflow│
                         │                          │
                         │ Attempts                 │
                         │ Stopping Rules           │
                         │ Human Escalation         │
                         └────────────┬─────────────┘
                                      ↓
                         ┌──────────────────────────┐
                         │     Supabase PostgreSQL  │
                         │                          │
                         │ payments                 │
                         │ customer profiles        │
                         │ recovery actions         │
                         │ recovery attempts        │
                         │ audit events             │
                         └────────────┬─────────────┘
                                      │
                                      ↕
                         ┌──────────────────────────┐
                         │     Razorpay Test Mode   │
                         │                          │
                         │ Recovery Payment Links   │
                         └──────────────────────────┘
```

---

# How the AI Decision Engine Works

The decision engine combines four major layers:

```text
Layer 1
Prediction

Layer 2
Optimization

Layer 3
Policy

Layer 4
Workflow
```

### Layer 1 — Prediction

Estimate recovery probability.

```text
Payment Context
      ↓
ML Model
      ↓
Recovery Probability
```

### Layer 2 — Optimization

Evaluate candidate interventions.

```text
Candidate Intervention
      ↓
ML Prediction
      ↓
Expected Recovery Value
```

### Layer 3 — Policy

Determine whether automatic execution is permitted.

```text
Prediction + Payment Context
             ↓
       Policy Engine
             ↓
    AUTO / HUMAN REVIEW
```

### Layer 4 — Workflow

Manage the actual recovery lifecycle.

```text
Recommendation
      ↓
Attempt
      ↓
Outcome
      ↓
Continue / Stop / Escalate
```

---

# Recovery Probability

The deployed model predicts the probability of successful recovery.

The model operates on engineered payment, customer, temporal, and intervention features.

The prediction is used as:

```text
recovery_probability
```

and is also exposed as a percentage:

```text
recovery_probability_percent
```

Example:

```text
0.8356
```

becomes:

```text
83.56%
```

---

# Intervention Optimization

AgentReady evaluates four candidate interventions:

```text
retry_now
retry_later
request_alternative_payment
request_card_update
```

For each intervention:

```text
Payment Context
      +
Candidate Intervention
      ↓
ML Model
      ↓
Recovery Probability
      ↓
Expected Recovery Value
```

The candidates are sorted by expected recovery value.

The highest-value candidate becomes:

```text
recommended_intervention
```

---

# Expected Recovery Value

AgentReady uses:

```text
ERV = Amount × Recovery Probability
```

For example:

```text
Amount = ₹2,499

Recovery Probability = 83.56%

ERV
= 2499 × 0.8356
≈ ₹2,088.16
```

The important distinction is:

> **ERV represents model-estimated recovery opportunity, not guaranteed recovered revenue.**

It should therefore not be presented as money already recovered.

---

# Policy Engine and Guardrails

The policy engine exists between prediction and action.

Current policy boundaries include:

```text
Maximum automatic recovery amount:
₹15,000

Minimum probability for automatic execution:
80%

Maximum previous payment attempts:
1

Maximum previous recovery attempts:
1
```

These constraints produce a decision:

```text
AUTO_EXECUTE
```

or:

```text
HUMAN_REVIEW
```

### Example

A payment may have:

```text
Amount:
₹12,999

Recovery Probability:
78.67%

Expected Recovery Value:
₹10,226.31
```

Even though the expected recovery value is large, the system routes it to:

```text
HUMAN_REVIEW
```

because the recovery probability is below the automatic-execution threshold.

This demonstrates that:

> **Economic opportunity does not automatically override operational policy.**

---

# Bounded Recovery Workflow

The recovery workflow is explicitly bounded.

Current maximum:

```text
2 recovery attempts
```

The workflow checks:

### Rule 1 — Previous success

If a previous attempt succeeded:

```text
STOP
```

No additional recovery attempt is required.

---

### Rule 2 — Existing pending attempt

If a recovery attempt is already pending:

```text
Reuse existing pending workflow
```

This prevents duplicate pending actions.

---

### Rule 3 — Maximum attempts

If the payment has already reached the maximum number of attempts:

```text
HUMAN_REVIEW
```

---

### Rule 4 — Next available intervention

If another intervention is available:

```text
CONTINUE
```

with the next intervention.

---

# Idempotency and Duplicate Prevention

Financial APIs can receive repeated requests because of:

- Browser refreshes
- Network retries
- Client retries
- Duplicate button clicks
- Background job retries

AgentReady therefore includes duplicate-prevention logic.

## Recovery recommendations

Before creating a new recommendation, the backend checks whether an existing recommended action already exists for the payment.

If one exists:

```text
Existing Recommendation
        ↓
Reuse
```

instead of:

```text
Create another recommendation
```

---

## Recovery workflow attempts

Before creating a new pending attempt, the workflow checks for an existing pending attempt.

This prevents:

```text
Attempt 1
Attempt 1
Attempt 1
Attempt 1
```

from being created accidentally.

---

# Human-in-the-Loop

AgentReady does not attempt to automate every payment.

Human review is triggered when policy conditions are violated.

Examples:

```text
Recovery probability too low
```

or:

```text
Previous attempts too high
```

or:

```text
Previous recovery attempts too high
```

or:

```text
Payment exceeds automatic-execution amount limit
```

This gives merchants a control mechanism:

```text
AI recommends
      ↓
Policy evaluates
      ↓
Safe cases → automatic path
Riskier cases → human review
```

---

# Recovery Copilot

AgentReady includes a recovery copilot designed for merchant operators.

Example questions:

```text
Which failed payments should I prioritize?

How much revenue is currently at risk?

Which payments need human review?

What should we do with cust_001?
```

The copilot grounds its responses in live system data.

Its reasoning pipeline is:

```text
Merchant Question
       ↓
Intent Detection
       ↓
Live Failed Payments
       ↓
Recovery Model
       ↓
Intervention Optimizer
       ↓
Policy Engine
       ↓
Grounded Response
```

The copilot is intentionally deterministic and grounded in the recovery engine rather than acting as an unconstrained generic chatbot.

---

# Razorpay Integration

AgentReady integrates with **Razorpay Test Mode** for sandbox recovery Payment Links.

The integration uses the Razorpay Python SDK.

The recovery service:

1. Validates the recovery amount.
2. Generates a deterministic reference ID.
3. Creates a Razorpay Test Mode Payment Link.
4. Associates AgentReady payment/customer metadata.
5. Returns the Payment Link identifier and short URL.
6. Supports fetching Payment Link status.

Example provider metadata:

```text
agentready_payment_id
agentready_customer_id
```

---

## Razorpay Test Mode Safety

The integration uses:

```text
Razorpay Test Mode
```

No real customer money is processed.

A successfully created Test Mode Payment Link demonstrates:

```text
AgentReady
    ↓
FastAPI
    ↓
Razorpay SDK
    ↓
Razorpay Test Mode
```

It does **not** mean that the displayed Expected Recovery Value has actually been recovered.

Actual recovered revenue should only be counted after a successful payment outcome has been observed and persisted.

---

# Database Architecture

AgentReady uses **Supabase PostgreSQL** for persistence.

Core entities include:

```text
payments
customer_recovery_profiles
recovery_actions
recovery_attempts
audit_events
```

---

## Payments

Stores failed payment information.

Representative fields:

```text
id
customer_id
amount
currency
payment_status
failure_reason
created_at
payment_method
```

---

## Customer Recovery Profiles

Stores recovery-related customer history.

Representative fields include:

```text
customer_id
customer_success_rate
customer_tenure_days
historical_payments
historical_failed_payments
historical_recovered_payments
historical_recovery_rate
days_since_last_success
previous_attempts
previous_recovery_attempts
previous_recovery_success
customer_recovery_history
updated_at
```

---

## Recovery Actions

Stores AI-generated recovery recommendations.

Representative fields:

```text
id
payment_id
strategy
priority
priority_score
status
created_at
provider
provider_reference
provider_url
provider_status
```

---

## Recovery Attempts

Stores workflow execution state.

Representative fields:

```text
id
payment_id
attempt_number
intervention
status
failure_reason
recovery_action_id
created_at
completed_at
```

---

## Audit Events

Stores system-level recovery decision events.

Examples:

```text
batch_recovery_analysis
payment_analysis
ml_recovery_prediction
recovery_recommendation_reused
recovery_attempt_created
recovery_workflow_decision
recovery_execution_blocked
```

---

# Audit Trail

The frontend exposes an operational audit trail.

The purpose is to answer:

```text
What happened?
When did it happen?
What decision was made?
Which intervention was involved?
What was the outcome?
Why did the system stop or escalate?
```

Example event:

```text
Recovery Execution Blocked

Decision:
—

Intervention:
retry_later

Status:
blocked

Reason:
Maximum recovery attempts reached
```

This is particularly important for financial automation because the system should be able to explain its operational history.

---

# Machine Learning Model

AgentReady currently deploys:

```text
Logistic Regression
```

with regularization:

```text
C = 0.03
```

The model uses:

```text
38 engineered features
```

The training pipeline:

```text
Synthetic Recovery Dataset
          ↓
Feature Engineering
          ↓
Remove Leakage
          ↓
Stratified Train/Test Split
          ↓
Candidate Models
          ↓
Cross Validation
          ↓
Hyperparameter Evaluation
          ↓
Calibration Analysis
          ↓
Final Model
          ↓
joblib Artifact
          ↓
FastAPI Prediction Service
```

---

# Feature Engineering

The deployed model uses 38 engineered features.

Feature groups include:

```text
Payment characteristics
Customer history
Failure context
Temporal context
Attempt history
Recovery history
Intervention context
```

The production prediction service mirrors the same feature engineering logic used during training.

This is important because training and inference must use consistent feature construction.

---

# Model Evaluation

AgentReady does not rely on accuracy alone.

The model is evaluated using:

- Accuracy
- Precision
- Recall
- F1 Score
- ROC-AUC
- PR-AUC
- Brier Score
- 5-fold cross-validation
- Train/CV gap
- Probability calibration

---

# Held-Out Test Performance

Current deployed model:

| Metric | Result |
|---|---:|
| Accuracy | 78.1% |
| Precision | 79.6% |
| Recall | 94.5% |
| F1 Score | 86.4% |
| ROC-AUC | 77.9% |
| PR-AUC | 89.7% |
| Brier Score | 0.154 |

The high recall is useful for identifying recoverable cases, while probability quality is further examined using calibration analysis.

---

# Cross-Validation

The model was evaluated using 5-fold cross-validation.

| Metric | Result |
|---|---:|
| ROC-AUC | 76.8% |
| PR-AUC | 89.3% |
| F1 Score | 85.8% |
| Recall | 93.5% |
| Train/CV ROC-AUC Gap | 0.76% |

The train/CV gap is:

```text
0.76%
```

A small gap provides evidence that the model is not relying purely on training-set performance.

---

# Model Comparison

Candidate models were evaluated before selecting the deployed model.

| Model | CV ROC-AUC | Train/CV Gap |
|---|---:|---:|
| Logistic Regression | 77.0% | 0.7% |
| XGBoost | 76.6% | 8.2% |
| HistGradientBoosting | 76.5% | 6.2% |
| Random Forest | 75.6% | 13.3% |

Logistic Regression was selected because it provided competitive validation performance with a substantially smaller train/CV gap.

This is an important distinction:

> **The most complex model was not automatically selected.**

Model selection considered both predictive performance and generalization behavior.

---

# Probability Calibration

Because recovery decisions use predicted probabilities, calibration matters.

A probability of:

```text
80%
```

should ideally correspond to approximately:

```text
80 recoveries per 100 similar cases
```

over a sufficiently large population.

AgentReady evaluates predicted probability against observed recovery frequency across 10 probability bins.

Examples:

| Probability Range | Predicted | Actual |
|---|---:|---:|
| 0.5–0.6 | 55.3% | 55.1% |
| 0.6–0.7 | 65.2% | 65.8% |
| 0.7–0.8 | 75.3% | 73.6% |
| 0.8–0.9 | 85.3% | 86.5% |
| 0.9–1.0 | 94.0% | 93.3% |

Calibration is particularly relevant because AgentReady uses probability thresholds inside the policy engine.

---

# Batch Recovery Analysis

A key part of AgentReady is portfolio-level recovery analysis.

Instead of analyzing only one payment:

```text
Payment A
```

the system can analyze the failed-payment portfolio:

```text
Payment A
Payment B
Payment C
Payment D
Payment E
Payment F
        ↓
Batch Recovery Analysis
        ↓
Rank Opportunities
        ↓
Apply Policy
```

The batch endpoint returns:

```text
payment_count
total_revenue_at_risk
total_expected_recovery
recovery_opportunity_rate
average_recovery_probability
auto_recovery_count
human_review_count
results
```

---

# Current Demo Results

A current batch analysis contains:

```text
6 failed payments

₹30,094
Revenue at risk

₹19,144.82
Model-estimated expected recovery

63.62%
Recovery opportunity

62.56%
Average recovery probability

3
Automatic candidates

3
Human-review candidates
```

These numbers are generated by the deployed backend.

Because the system includes time-dependent features such as time since failure, probabilities and ERV can change slightly between analyses.

---

# Example Recovery Decisions

## cust_demo_001

```text
Amount:
₹3,499

Failure:
insufficient_funds

Intervention:
retry_later

Recovery Probability:
82.37%

Expected Recovery Value:
₹2,882.13

Policy:
AUTO_EXECUTE
```

---

## cust_001

```text
Amount:
₹2,499

Failure:
insufficient_funds

Intervention:
retry_later

Recovery Probability:
83.56%

Expected Recovery Value:
₹2,088.16

Policy:
AUTO_EXECUTE
```

---

## cust_002

```text
Amount:
₹8,999

Failure:
card_declined

Intervention:
request_alternative_payment

Recovery Probability:
27.33%

Expected Recovery Value:
₹2,459.43

Policy:
HUMAN_REVIEW
```

Reasons include:

```text
Recovery probability below automatic threshold
Previous payment attempts exceeded limit
Previous recovery attempts exceeded limit
```

---

## cust_003

```text
Amount:
₹1,499

Failure:
network_error

Intervention:
retry_later

Recovery Probability:
96.59%

Expected Recovery Value:
₹1,447.88

Policy:
AUTO_EXECUTE
```

---

## cust_004

```text
Amount:
₹12,999

Failure:
insufficient_funds

Intervention:
retry_later

Recovery Probability:
78.67%

Expected Recovery Value:
₹10,226.31

Policy:
HUMAN_REVIEW
```

This is an important example because `cust_004` has the largest Expected Recovery Value but is still not automatically executed.

The reason:

```text
78.67% < 80% automatic threshold
```

This demonstrates that AgentReady's policy layer can override an attractive economic opportunity when confidence is insufficient for automatic execution.

---

## cust_005

```text
Amount:
₹599

Failure:
expired_card

Intervention:
request_card_update

Recovery Probability:
6.83%

Expected Recovery Value:
₹40.91

Policy:
HUMAN_REVIEW
```

---

# API Reference

## Health

```http
GET /health
```

Returns backend health information.

---

## Failed Payments

```http
GET /payments
```

Returns failed payment records used by the dashboard.

---

## Analyze Payment

```http
POST /payments/{payment_id}/analyze
```

Analyzes an individual payment and produces a recovery recommendation.

---

## Create or Reuse Recovery Recommendation

```http
POST /payments/{payment_id}/recover
```

Creates a persisted recovery recommendation.

The endpoint is idempotent with respect to an existing recommended action.

---

## Batch Recovery Analysis

```http
POST /recovery/batch
```

Analyzes the current failed-payment portfolio.

Example response structure:

```json
{
  "success": true,
  "data": {
    "payment_count": 6,
    "total_revenue_at_risk": 30094,
    "total_expected_recovery": 19144.82,
    "recovery_opportunity_percent": 63.62,
    "auto_recovery_count": 3,
    "human_review_count": 3,
    "results": []
  }
}
```

---

## Recovery Workflow

```http
POST /payments/{payment_id}/recovery-workflow
```

Evaluates the next bounded recovery workflow state.

Possible outcomes include:

```text
CONTINUE
PENDING
HUMAN_REVIEW
STOP
```

---

## Recovery Attempts

```http
GET /payments/{payment_id}/recovery-attempts
```

Returns recovery attempts for a payment.

---

## Update Recovery Attempt

```http
PATCH /recovery-attempts/{attempt_id}
```

Updates the attempt outcome.

Supported final statuses include:

```text
success
failed
```

---

## Audit Events

```http
GET /audit-events
```

Returns persisted recovery and decision events.

---

# Frontend

The frontend is a Next.js + TypeScript recovery command center.

The dashboard includes:

### Recovery Copilot

Interactive operational questions.

### Recovery Intelligence

Portfolio-level revenue recovery metrics.

### Recovery Opportunity

Model-estimated recovery opportunity.

### Decision Queue

Prioritized recovery recommendations.

### Failed Payments

Live failed payment data retrieved from the backend.

### Recovery History

Persisted recommendations and workflow history.

### Audit Trail

Historical system decisions and workflow outcomes.

### Model Validation

Evidence-based ML evaluation.

### Probability Calibration

Predicted vs observed recovery probabilities.

---

# Backend

The backend is implemented using:

```text
Python
FastAPI
Supabase
scikit-learn
Razorpay Python SDK
```

The backend acts as the central orchestration layer between:

```text
Frontend
    ↓
FastAPI
    ↓
Recovery Intelligence
    ↓
Supabase
    +
Razorpay Test Mode
```

The frontend does not contain hardcoded recovery decisions.

Recovery metrics and recommendations are generated by the backend.

---

# Project Structure

```text
AgentReady/
│
├── backend/
│   │
│   ├── app/
│   │   ├── main.py
│   │   └── supabase_client.py
│   │
│   ├── ml/
│   │   ├── models/
│   │   │   └── agentready_recovery_model.joblib
│   │   │
│   │   ├── model_features.py
│   │   ├── prediction_service.py
│   │   ├── intervention_optimizer.py
│   │   ├── policy_engine.py
│   │   ├── recovery_context.py
│   │   ├── recovery_workflow.py
│   │   ├── recovery_agent.py
│   │   └── recovery_attempt_service.py
│   │
│   ├── razorpay_client.py
│   ├── razorpay_recovery_service.py
│   └── requirements.txt
│
├── frontend/
│   ├── app/
│   │   ├── page.tsx
│   │   ├── layout.tsx
│   │   └── globals.css
│   │
│   ├── public/
│   └── package.json
│
├── tests/
│
├── docs/
│
├── .cursor/
│   └── rules/
│
├── .gitignore
├── requirements.txt
└── README.md
```

---

# Technology Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js |
| Language | TypeScript |
| Backend | Python |
| API Framework | FastAPI |
| Database | Supabase PostgreSQL |
| ML | scikit-learn |
| Model Serialization | joblib |
| Payment Provider | Razorpay Test Mode |
| Payment SDK | Razorpay Python SDK |
| API Communication | REST |
| Frontend Deployment | Vercel |
| Backend Deployment | Render |
| Version Control | Git + GitHub |

---

# Deployment

## Frontend

The frontend is deployed on:

```text
Vercel
```

Live application:

```text
https://agent-ready-psi.vercel.app/
```

---

## Backend

The backend is deployed on:

```text
Render
```

Live API:

```text
https://agentready-2.onrender.com
```

Health endpoint:

```text
https://agentready-2.onrender.com/health
```

---

## Production-style Flow

```text
User
 ↓
Vercel Frontend
 ↓
Render FastAPI Backend
 ↓
Supabase PostgreSQL
 ↓
ML Recovery Engine
 ↓
Policy + Workflow
 ↓
Razorpay Test Mode
```

---

# Environment Variables

Backend:

```text
SUPABASE_URL=your_supabase_project_url
SUPABASE_SECRET_KEY=your_server_side_key

RAZORPAY_KEY_ID=your_test_key_id
RAZORPAY_KEY_SECRET=your_test_key_secret
```

Frontend:

```text
NEXT_PUBLIC_API_URL=http://127.0.0.1:8001
```

For deployment, `NEXT_PUBLIC_API_URL` should point to the deployed backend.

Example:

```text
NEXT_PUBLIC_API_URL=https://agentready-2.onrender.com
```

---

# Security

Secrets are kept outside the source code.

The repository must never contain:

```text
SUPABASE_SECRET_KEY
RAZORPAY_KEY_SECRET
```

or any other production credential.

Environment variables are used for server-side secrets.

The frontend only receives information required for the dashboard and recovery workflows.

---

# Local Setup

## Prerequisites

Install:

```text
Python
Node.js
Git
```

---

# Backend Setup

Navigate to:

```powershell
cd D:\AgentReady\backend
```

Create a virtual environment:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Create the backend environment configuration.

Then start FastAPI:

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

Backend:

```text
http://127.0.0.1:8001
```

Swagger:

```text
http://127.0.0.1:8001/docs
```

---

# Frontend Setup

Open a second terminal:

```powershell
cd D:\AgentReady\frontend
```

Install dependencies:

```powershell
npm install
```

Start the development server:

```powershell
npm run dev
```

Frontend:

```text
http://localhost:3000
```

---

# Testing

AgentReady contains an automated test suite covering core recovery intelligence behavior.

Current milestone:

```text
23 tests passing
```

The test suite covers areas including:

```text
Recovery prediction
Intervention optimization
Policy decisions
Recovery workflow
Maximum attempt stopping
Duplicate prevention
Recovery Copilot behavior
```

Run tests from the backend environment with the project's configured test command.

---

# Security and Safety

AgentReady is intentionally designed with multiple boundaries.

## 1. Prediction is not authorization

The ML model does not directly execute financial actions.

Instead:

```text
ML Prediction
      ↓
Optimizer
      ↓
Policy Engine
      ↓
Action Permission
```

---

## 2. Automatic execution is bounded

Automatic execution is subject to:

```text
Amount threshold
Probability threshold
Previous attempt limits
Previous recovery attempt limits
```

---

## 3. Recovery loops are bounded

The workflow has:

```text
Maximum 2 recovery attempts
```

After the limit:

```text
HUMAN_REVIEW
```

---

## 4. Test Mode

The Razorpay integration uses:

```text
Razorpay Test Mode
```

No real customer money is processed.

---

## 5. Synthetic Data

The current demonstration uses synthetic/demo payment and recovery-history data.

No real customer information is required for the demo.

---

# Demo Walkthrough

The strongest demonstration follows this sequence.

## 1. Open AgentReady

Open:

```text
https://agent-ready-psi.vercel.app/
```

---

## 2. Show the failed-payment portfolio

Start with:

```text
6 failed payments
₹30,094 revenue at risk
```

---

## 3. Run the recovery analysis

Click:

```text
Run Recovery Agent
```

The system calls:

```http
POST /recovery/batch
```

---

## 4. Show the recovery opportunity

Highlight:

```text
₹19,144.82
Model-estimated expected recovery
```

Then:

```text
63.62%
Recovery opportunity
```

---

## 5. Show AUTO vs HUMAN REVIEW

Highlight:

```text
3 AUTO
3 HUMAN REVIEW
```

Explain that the policy engine prevents the ML model from directly controlling financial actions.

---

## 6. Show the decision queue

Demonstrate that different payments receive different interventions.

For example:

```text
Insufficient Funds
      ↓
Retry Later
```

while:

```text
Expired Card
      ↓
Request Card Update
```

---

## 7. Show the highest-value opportunity

Open:

```text
cust_004
```

Show:

```text
₹12,999
78.67% probability
₹10,226.31 ERV
HUMAN_REVIEW
```

Explain:

> Even though this is the largest recovery opportunity, AgentReady does not automatically act because the predicted recovery probability is below the configured automatic threshold.

---

## 8. Demonstrate the bounded workflow

Show:

```text
Attempt 1
      ↓
Outcome
      ↓
Attempt 2
      ↓
Stop / Human Review
```

---

## 9. Show the audit trail

Demonstrate:

```text
ML prediction
Payment analysis
Workflow decision
Recovery attempt
Execution blocked
```

This proves that decisions are traceable.

---

## 10. Show the model validation

Scroll to:

```text
AI Recovery Model Evaluation
```

Highlight:

```text
38 engineered features
78.1% accuracy
94.5% recall
77.9% ROC-AUC
89.7% PR-AUC
0.154 Brier score
5-fold CV
0.76% train/CV gap
```

Then show calibration.

---

## 11. Show Razorpay integration

Explain that recovery Payment Links are generated through Razorpay Test Mode.

Important:

```text
Sandbox connectivity
≠
Actual recovered revenue
```

---

# Current Demo Results

A current deployed batch analysis returns approximately:

```text
╔══════════════════════════════════════════════╗
║              AGENTREADY                      ║
╠══════════════════════════════════════════════╣
║ Failed Payments                    6         ║
║ Revenue at Risk              ₹30,094         ║
║ Expected Recovery              ₹19,144.82    ║
║ Recovery Opportunity              63.62%     ║
║ Average Probability               62.56%     ║
║                                              ║
║ Automatic Candidates                 3      ║
║ Human Review                         3      ║
╚══════════════════════════════════════════════╝
```

These are **model-generated demo metrics**, not claims of actual recovered revenue.

---

# Limitations

AgentReady is a hackathon prototype.

The current system uses:

```text
Synthetic payment data
Synthetic customer recovery history
Synthetic training data
Razorpay Test Mode
```

The ML model therefore should not be interpreted as production financial advice.

The displayed:

```text
Expected Recovery Value
```

is an estimated opportunity.

It is not:

```text
Guaranteed recovered revenue
```

and it is not a causal estimate of the exact amount a specific intervention will recover.

---

# Production Considerations

A production deployment would require additional capabilities such as:

### Authentication

Merchant and operator authentication.

### Authorization

Role-based access control for financial actions.

### Privacy

Data minimization and stronger customer-data controls.

### Monitoring

Real-time monitoring of:

```text
Recovery rate
Model drift
Provider failures
Policy violations
Workflow failures
```

### Model Governance

Additional validation across:

```text
Merchant segments
Payment methods
Regions
Failure types
Time periods
```

### Outcome Feedback

Successful and unsuccessful recovery outcomes should continuously feed model evaluation and retraining pipelines.

### Fraud and Risk Controls

Recovery automation should operate alongside payment fraud and risk systems.

### Observability

Production deployment would require:

```text
Structured logs
Metrics
Tracing
Alerting
Error monitoring
```

---

# Future Roadmap

## Phase 1 — Current Prototype

```text
✓ Failed payment detection
✓ Customer recovery context
✓ ML recovery prediction
✓ Intervention optimization
✓ Expected Recovery Value
✓ Policy engine
✓ AUTO / HUMAN_REVIEW
✓ Bounded workflow
✓ Idempotency
✓ Audit trail
✓ Recovery Copilot
✓ Razorpay Test Mode
✓ Deployed frontend
✓ Deployed backend
```

---

## Phase 2 — Production Recovery

```text
Live payment outcomes
       ↓
Actual recovery measurement
       ↓
Outcome feedback
       ↓
Model monitoring
       ↓
Model retraining
```

---

## Phase 3 — Merchant-Specific Intelligence

Different merchants have different:

```text
Customer behavior
Payment methods
Risk tolerance
Recovery economics
Business rules
```

AgentReady could therefore support merchant-specific recovery policies and models.

---

## Phase 4 — Recovery Strategy Experimentation

The platform could compare recovery strategies using controlled experiments:

```text
Retry timing
Payment method switching
Customer messaging
Recovery channels
Intervention sequences
```

with appropriate measurement and governance.

---

## Phase 5 — Continuous Recovery Intelligence

The long-term architecture becomes:

```text
Observe
   ↓
Predict
   ↓
Prioritize
   ↓
Govern
   ↓
Act
   ↓
Observe Outcome
   ↓
Evaluate
   ↓
Learn
   ↓
Improve
```

---

# Why This Fits the AI Revenue Recovery Track

AgentReady directly addresses the core revenue-recovery problem.

## Detect revenue at risk

```text
Failed Payments
      ↓
Portfolio Analysis
```

## Determine the right intervention

```text
ML Prediction
      ↓
Candidate Intervention Evaluation
      ↓
Optimization
```

## Quantify recovery opportunity

```text
Payment Amount
      ×
Recovery Probability
      =
Expected Recovery Value
```

## Execute within boundaries

```text
Policy Engine
      ↓
AUTO / HUMAN REVIEW
```

## Manage recovery workflow

```text
Attempt
      ↓
Outcome
      ↓
Continue / Stop / Escalate
```

## Handle failures safely

```text
Maximum Attempts
      ↓
Human Review
```

## Maintain an audit trail

```text
Prediction
Decision
Action
Outcome
Workflow
```

---

# The Central Product Question

AgentReady is designed around one question:

> **"Given all the failed payments in front of a merchant, where should the merchant intervene, what should they do, and when should the system stop?"**

The system answers this using:

```text
Predictive Intelligence
        +
Expected Value
        +
Policy Governance
        +
Bounded Automation
        +
Auditability
```

---

# Key Design Principle

The most important architectural principle in AgentReady is:

```text
                 ┌──────────────────┐
                 │   ML Prediction  │
                 └────────┬─────────┘
                          ↓
                 ┌──────────────────┐
                 │   Optimization   │
                 └────────┬─────────┘
                          ↓
                 ┌──────────────────┐
                 │ Policy Guardrail │
                 └────────┬─────────┘
                          ↓
              ┌───────────┴───────────┐
              ↓                       ↓
        AUTO EXECUTE            HUMAN REVIEW
              ↓                       ↓
              └───────────┬───────────┘
                          ↓
                    WORKFLOW
                          ↓
                       AUDIT
```

This ensures that:

> **AI can recommend an action without becoming an uncontrolled financial actor.**

---

# Live Demo

### Frontend

```text
https://agent-ready-psi.vercel.app/
```

### Backend

```text
https://agentready-2.onrender.com
```

### Health Check

```text
https://agentready-2.onrender.com/health
```

### API Documentation

When running locally:

```text
http://127.0.0.1:8001/docs
```

---

# Final Summary

AgentReady transforms failed-payment recovery from a simple retry mechanism into a predictive decision system.

```text
FAILED PAYMENT
      ↓
UNDERSTAND CONTEXT
      ↓
PREDICT RECOVERY
      ↓
EVALUATE INTERVENTIONS
      ↓
CALCULATE EXPECTED VALUE
      ↓
APPLY POLICY
      ↓
AUTOMATE OR ESCALATE
      ↓
BOUND THE WORKFLOW
      ↓
OBSERVE OUTCOME
      ↓
AUDIT
```

The system is designed to help merchants recover more intelligently while keeping financial automation:

```text
Predictive
Explainable
Bounded
Idempotent
Auditable
Human-governed
```

---

# Built For

## Razorpay AI Buildathon 2026

### AI Revenue Recovery Track

**AgentReady**

> ### Predict. Prioritize. Govern. Recover.