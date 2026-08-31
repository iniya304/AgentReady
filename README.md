# AgentReady

A full-stack hackathon project for preparing and shipping agent-ready workflows with a Next.js frontend, FastAPI backend, and Supabase as the source of truth.

## Project Overview

AgentReady is a web application that helps teams design, run, and review AI-assisted workflows with explicit APIs, auditable actions, and guarded financial operations. This repository currently contains project foundation only; application code will follow.

## Problem

Teams building AI agents often mix frontend secrets, unvalidated payments, and ad-hoc data. That makes systems hard to trust, hard to test, and unsafe for real money movement.

## Solution

AgentReady keeps a clear split: the Next.js client talks only to FastAPI; FastAPI owns Razorpay, Supabase service credentials, validation, and audit logs. LangGraph orchestrates agents behind backend guardrails so financial actions never run unrestricted.

## Architecture

```
[ Next.js + TypeScript ]  -->  [ FastAPI APIs ]  -->  [ Supabase PostgreSQL ]
                                      |
                                      +--> Razorpay (test mode)
                                      +--> LangGraph (agent orchestration)
```

- Frontend never holds secret keys.
- Persistent business data lives in Supabase.
- Request/response contracts are explicit on both sides.

## Technology Stack

| Layer | Choice |
| --- | --- |
| Frontend | Next.js, TypeScript |
| Backend | Python, FastAPI |
| Database | Supabase PostgreSQL |
| Payments | Razorpay (test mode) |
| AI orchestration | LangGraph |

## Features

Placeholder — product features will be listed here as they are implemented.

## Project Structure

```
AgentReady/
├── .cursor/rules/architecture.mdc
├── .gitignore
└── README.md
```

Frontend, backend, and related packages are not created yet.

## Local Development

Not applicable until the application is scaffolded. Do not install frontend or backend dependencies until that work starts.

Expected later flow (placeholder):

1. Configure environment variables from a documented example file.
2. Run the FastAPI backend.
3. Run the Next.js frontend.
4. Point the frontend at backend APIs only.

## Environment Variables

Secrets belong in ignored `.env` files, never in source control or the frontend bundle.

Typical categories (names TBD when apps exist):

- Backend: Supabase URL, anon key (if used server-side), **service role key**, Razorpay **key secret**, database URLs.
- Frontend: public backend base URL and public Razorpay **key id** only if required by official client checkout — never Razorpay secret or Supabase service role.

## Testing

Placeholder. When code exists, tests should cover the frontend → backend → database path, not isolated mocks that hide contract drift.

## Deployment

Placeholder. Keep the stack small enough for a five-day hackathon. Prefer one frontend host, one backend host, and managed Supabase.

## Security

- No secret API keys in the frontend.
- Razorpay secrets and Supabase service-role credentials stay on the backend.
- Agents must not perform unrestricted financial operations; payments go through backend validation.
- Log agent actions and important audit events.
- Never invent Razorpay endpoints or parameters; verify official docs.

## Roadmap

1. Foundation (this step): ignore rules, README, Cursor architecture rules.
2. Backend and frontend scaffolds with explicit APIs.
3. Auth, core data model in Supabase, and UI flows.
4. LangGraph agents with guardrails and audit logging.
5. Razorpay test-mode payments with backend validation.
6. End-to-end tests and hackathon demo polish.
