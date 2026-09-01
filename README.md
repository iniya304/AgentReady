# AgentReady

Full-stack hackathon project: Next.js frontend and FastAPI backend.

## Project Overview

AgentReady currently has frontend and backend foundations only. Database, payments, AI agents, and the dashboard are not implemented yet.

## Problem

Placeholder — to be filled when product scope is finalized.

## Solution

Placeholder — to be filled when product scope is finalized.

## Architecture

```
[ Next.js + TypeScript ]  -->  [ FastAPI APIs ]
```

The frontend talks to the backend over HTTP. CORS allows local Next.js (`http://localhost:3000`) to call the API.

## Technology Stack

| Layer | Choice | Status |
| --- | --- | --- |
| Frontend | Next.js, TypeScript, Tailwind CSS | Foundation |
| Backend | Python, FastAPI | Foundation (`GET /health`) |
| Database | Supabase PostgreSQL | Not implemented |
| Payments | Razorpay (test mode) | Not implemented |
| AI orchestration | LangGraph | Not implemented |

## Features

- Frontend starter app (App Router)
- Backend `GET /health` JSON endpoint
- CORS for local frontend → backend calls

## Project Structure

```
AgentReady/
├── .cursor/rules/architecture.mdc
├── .gitignore
├── README.md
├── backend/
│   ├── .venv/                 # local virtualenv (gitignored)
│   ├── app/
│   │   ├── __init__.py
│   │   └── main.py
│   └── requirements.txt
├── docs/
├── frontend/
│   ├── .env.example
│   ├── app/
│   ├── public/
│   └── package.json
└── tests/
```

## Local Development

### Backend

From `backend/` (after the local venv exists and packages are installed):

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Health check: `http://127.0.0.1:8000/health`

### Frontend

From `frontend/` (after `npm install`):

```powershell
Copy-Item .env.example .env.local
npm run dev
```

App: `http://localhost:3000`

Do not install packages globally. Use `frontend/node_modules` and `backend/.venv` only.

## Environment Variables

`frontend/.env.example` documents `NEXT_PUBLIC_API_URL` (public backend URL, no secrets). Copy to `.env.local` for local use. `.env` files are gitignored.

No backend secrets are required for this foundation.

## Testing

`tests/` is reserved. No test suite yet.

## Deployment

Not configured.

## Security

- No secret API keys in the frontend.
- Do not commit `.env` files or `backend/.venv`.

## Roadmap

1. Frontend and backend foundations (current).
2. Auth, Supabase, and core APIs.
3. Dashboard UI.
4. LangGraph agents with guardrails.
5. Razorpay test-mode payments.
