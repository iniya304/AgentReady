# 🚀 AgentReady

### Predictive Revenue Recovery Agent for Failed Payments

> **AgentReady doesn't just detect failed payments — it decides which revenue is worth recovering, chooses the right intervention, and tracks the recovery workflow with bounded actions and an audit trail.**

Built for the **Razorpay AI Buildathon — AI Revenue Recovery Track**.

---

## 🎯 The Problem

A failed payment does not always mean lost revenue.

For a merchant, thousands of payment failures can happen because of:

* Insufficient funds
* Card declines
* Expired cards
* Temporary network failures
* Other payment failures

The challenge is deciding:

> **Which failed payments should the merchant pursue, what action should be taken, and when should the system stop trying?**

A simple retry mechanism treats every failure equally.

**AgentReady takes a different approach.**

---

# 💡 Our Solution

AgentReady is an **agentic revenue recovery system** that analyzes failed payments and determines the most appropriate recovery strategy.

The system is designed to evolve from reactive recovery into **predictive revenue recovery**.

### Current workflow

```text
Failed Payment
      ↓
Payment Analysis
      ↓
Failure Reason Detection
      ↓
Recovery Strategy
      ↓
Priority Scoring
      ↓
Bounded Recovery Action
      ↓
Recovery History
```

### Target predictive workflow

```text
Payment + Customer History
            ↓
     🧠 ML Risk Predictor
            ↓
   Recovery Probability
            ↓
  💰 Expected Recovery Value
            ↓
      🤖 Recovery Agent
            ↓
     Policy / Guardrails
            ↓
     ┌──────┴──────┐
     ↓             ↓
Auto Action    Human Review
     ↓             ↓
     └──────┬──────┘
            ↓
         Outcome
            ↓
    Recovered / Failed
            ↓
      Stop / Escalate
            ↓
     Audit + Metrics
```

---

# 🧠 What Makes AgentReady Different?

### 1. Predict before acting

Instead of treating every failed payment equally, AgentReady is designed to predict the probability that revenue will remain unrecovered.

Example:

```text
Payment: ₹12,999

Recovery Probability: 82%
Risk: HIGH

Expected Recovery Value:
₹7,447

Recommended Action:
Retry Later
```

This allows merchants to prioritize recovery based on **expected value**, rather than payment amount alone.

---

### 2. Recovery strategy selection

Different failure reasons require different interventions.

| Failure            | Recommended Strategy        |
| ------------------ | --------------------------- |
| Insufficient funds | Retry later                 |
| Card declined      | Request alternative payment |
| Network error      | Retry now                   |
| Expired card       | Request card update         |
| Unknown failure    | Manual review               |

The decision layer can combine payment context, prediction, priority and policy constraints.

---

### 3. Bounded actions

AgentReady is not designed to retry payments indefinitely.

A recovery workflow follows explicit limits:

```text
Attempt 1
   ↓
Recovery Action
   ↓
Observe Outcome
   ↓
Failed?
   ↓
Attempt 2
   ↓
Alternative Action
   ↓
Still Failed?
   ↓
STOP → Human Review
```

This prevents uncontrolled recovery loops.

---

### 4. Expected Recovery Value

The system can prioritize opportunities using:

```text
Expected Recovery Value
=
Payment Amount
×
Recovery Probability
×
Intervention Effectiveness
```

This creates a more meaningful recovery priority than simply sorting failed payments by amount.

---

### 5. Auditability

Every recovery decision is intended to be traceable:

```text
Payment
  ↓
Prediction
  ↓
Reason
  ↓
Decision
  ↓
Action
  ↓
Outcome
  ↓
Next Step
```

This allows a merchant to understand **why the agent made a decision**.

---

# 🏗️ Architecture

```text
                    ┌─────────────────────┐
                    │  Razorpay Test Mode │
                    └──────────┬──────────┘
                               │
                               ↓
                    ┌─────────────────────┐
                    │      AgentReady     │
                    │   FastAPI Backend   │
                    └──────────┬──────────┘
                               │
               ┌───────────────┴───────────────┐
               ↓                               ↓
       ┌────────────────┐             ┌────────────────┐
       │  ML Predictor  │             │ Supabase       │
       │ Recovery Risk  │             │ PostgreSQL     │
       └───────┬────────┘             └───────┬────────┘
               │                              │
               └──────────────┬───────────────┘
                              ↓
                    ┌─────────────────────┐
                    │  Recovery Decision  │
                    │      Engine         │
                    └──────────┬──────────┘
                               ↓
                    ┌─────────────────────┐
                    │ Policy & Guardrails │
                    └──────────┬──────────┘
                               ↓
                 ┌─────────────┴─────────────┐
                 ↓                           ↓
          Auto Recovery                Human Review
                 │                           │
                 └─────────────┬─────────────┘
                               ↓
                    ┌─────────────────────┐
                    │ Outcome & Evaluation│
                    └──────────┬──────────┘
                               ↓
                     Recovery Metrics
```

---

# 🛠️ Technology Stack

| Layer                  | Technology             |
| ---------------------- | ---------------------- |
| Frontend               | Next.js + TypeScript   |
| Backend                | Python + FastAPI       |
| Database               | Supabase PostgreSQL    |
| ML                     | Python + scikit-learn  |
| Agent / Decision Layer | Python recovery engine |
| Payments               | Razorpay Test Mode     |
| API Communication      | REST                   |
| Version Control        | Git + GitHub           |

---

# ✨ Current Features

* ✅ Failed payment dashboard
* ✅ Real payment data from Supabase
* ✅ FastAPI backend
* ✅ Payment retrieval API
* ✅ Payment creation API
* ✅ Payment failure analysis
* ✅ Failure-specific recovery strategies
* ✅ Recovery priority scoring
* ✅ Recovery action persistence
* ✅ Recovery history
* ✅ Frontend → backend → database integration
* ✅ CORS configuration
* ✅ Recovery action audit foundation

---

# 🧠 Predictive AI Roadmap

The next major layer is the **Predictive Revenue Risk Engine**.

### Model inputs

```text
Payment amount
Failure reason
Customer payment history
Previous attempts
Time since failure
Previous recovery outcomes
Intervention history
```

### Model output

```text
Probability of successful recovery
        +
Probability of remaining unrecovered
        +
Risk band
        +
Expected Recovery Value
```

The prediction will feed directly into the recovery decision engine.

---

# 📊 Batch Recovery Evaluation

AgentReady is designed to evaluate recovery across a batch rather than demonstrating only a single payment.

Example evaluation flow:

```text
100 Failed Payments
        ↓
Risk Prediction
        ↓
Prioritization
        ↓
Recovery Strategy Selection
        ↓
Bounded Actions
        ↓
Outcome Evaluation
        ↓
Recovered Revenue
```

Key metrics:

* Total revenue at risk
* Number of high-risk payments
* Automated recovery actions
* Human escalations
* Stopped workflows
* Recovery rate
* Expected recovery value
* Actual/simulated recovered revenue

All demo metrics will be generated from the system's evaluation pipeline rather than hardcoded into the frontend.

---

# 🔐 Safety & Guardrails

AgentReady follows a bounded-agent design.

The recovery system should:

* Never retry indefinitely
* Respect predefined action limits
* Escalate uncertain cases
* Record important decisions
* Separate recommendation from execution
* Use Razorpay test mode during development
* Never expose payment credentials or backend secrets in the frontend

---

# 📁 Project Structure

```text
AgentReady/
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── recovery_engine.py
│   │   └── supabase_client.py
│   │
│   └── requirements.txt
│
├── frontend/
│   ├── app/
│   │   └── page.tsx
│   ├── public/
│   └── package.json
│
├── docs/
│
├── tests/
│
├── .cursor/
│   └── rules/
│
├── .gitignore
└── README.md
```

---

# 🚀 Local Setup

## 1. Clone the repository

```bash
git clone https://github.com/iniya304/AgentReady.git
cd AgentReady
```

## 2. Backend

```bash
cd backend
```

Create and activate a virtual environment:

### Windows

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Run the API:

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Backend:

```text
http://127.0.0.1:8000
```

Health check:

```text
http://127.0.0.1:8000/health
```

---

## 3. Frontend

Open another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Frontend:

```text
http://localhost:3000
```

---

# 🔑 Environment Variables

Backend secrets must remain in environment variables.

Example:

```text
SUPABASE_URL=your_supabase_project_url
SUPABASE_SECRET_KEY=your_server_side_key
```

Frontend:

```text
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

**Never commit `.env` files or secret API keys.**

---

# 🧪 Development Status

### Completed

* [x] Full-stack project foundation
* [x] FastAPI backend
* [x] Next.js dashboard
* [x] Supabase integration
* [x] Payment data persistence
* [x] Payment analysis
* [x] Recovery strategy engine
* [x] Priority scoring
* [x] Recovery action persistence
* [x] Recovery history

### In Progress

* [ ] Predictive revenue-risk model
* [ ] Expected Recovery Value calculation
* [ ] Batch recovery evaluation
* [ ] Bounded recovery state machine
* [ ] Audit-event system
* [ ] Human escalation workflow
* [ ] Razorpay Test Mode integration
* [ ] End-to-end recovery outcome measurement

---

# 🏆 Hackathon Focus

AgentReady targets the **AI Revenue Recovery** problem:

> Detect revenue at risk, determine the right intervention, execute a bounded recovery workflow, and measure the resulting recovery.

The goal is not to build another payment dashboard.

The goal is to build a system that can answer:

> **"Given all the failed payments in front of me, where should I intervene, what should I do, and when should I stop?"**

---

# 🔭 Future Vision

AgentReady can evolve into a continuous revenue-recovery system that:

```text
Observe
   ↓
Predict
   ↓
Prioritize
   ↓
Act
   ↓
Observe Outcome
   ↓
Learn
   ↓
Act Better
```

The long-term objective is to move merchants from **reactive payment failure handling** to **predictive, measurable revenue recovery**.

---

## 👩‍💻 Built With

Built as a student project for the **Razorpay AI Buildathon 2026**.

**AgentReady — Recover revenue intelligently.**
