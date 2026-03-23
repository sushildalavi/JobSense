# JobSense

> Your AI-powered job search operating system. Discover jobs, tailor resumes, track applications, and automate interview scheduling — all from one intelligent dashboard.

[![CI](https://github.com/sushildalavi/JobSense/actions/workflows/ci.yml/badge.svg)](https://github.com/sushildalavi/JobSense/actions/workflows/ci.yml)
[![Deploy](https://github.com/sushildalavi/JobSense/actions/workflows/deploy.yml/badge.svg)](https://github.com/sushildalavi/JobSense/actions/workflows/deploy.yml)
[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green.svg)](https://fastapi.tiangolo.com)
[![Next.js 15](https://img.shields.io/badge/Next.js-15-black.svg)](https://nextjs.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Overview

JobSense is a production-grade agentic AI system built for AI/ML professionals and ambitious job seekers. It combines **intelligent job discovery**, **semantic matching**, **AI-driven resume tailoring**, **email intelligence**, and **calendar automation** into a unified workflow — replacing scattered spreadsheets, browser bookmarks, and manual follow-ups with a fully automated, auditable pipeline.

The system is built for engineers who want to see how frontier AI capabilities (LangGraph agents, pgvector embeddings, LLM-based entity extraction) connect into a real product — not just a demo.

---

## Architecture

```mermaid
graph TB
    subgraph "Browser"
        U[User]
    end

    subgraph "Frontend — Next.js 15"
        FE[React App<br/>shadcn/ui + Tailwind]
        TQ[TanStack Query]
        FM[Framer Motion]
    end

    subgraph "API Layer — FastAPI"
        API[FastAPI App<br/>JWT Auth + Google OAuth]
        WS[WebSocket Handler]
    end

    subgraph "Task Queue"
        RD[Redis Broker]
        CW[Celery Workers<br/>5 queues]
        CB[Celery Beat<br/>Scheduler]
    end

    subgraph "AI / Agent Layer"
        LG[LangGraph<br/>Orchestrator]
        OAI[OpenAI GPT-4o]
        ANT[Anthropic Claude]
        EMB[Embedding Service<br/>text-embedding-3-small]
    end

    subgraph "Integrations"
        APF[Apify<br/>LinkedIn/Greenhouse Scraper]
        GML[Gmail API<br/>Email Intelligence]
        GCL[Google Calendar API<br/>Event Automation]
    end

    subgraph "Data Store"
        PG[(PostgreSQL 16<br/>+ pgvector)]
        S3[(AWS S3<br/>File Storage)]
    end

    U --> FE
    FE --> TQ
    TQ --> API
    API --> RD
    API --> PG
    API --> S3
    RD --> CW
    CB --> RD
    CW --> LG
    CW --> APF
    CW --> GML
    CW --> GCL
    LG --> OAI
    LG --> ANT
    LG --> EMB
    EMB --> PG
    CW --> PG
    API --> WS
    WS --> FE
```

---

## Features

### Core Capabilities

| Feature | Description |
|---|---|
| **Intelligent Job Discovery** | Multi-source ingestion via Apify actors (LinkedIn, Greenhouse, Lever, custom scrapers). Deduplication via embedding similarity clustering. |
| **Semantic Job Matching** | pgvector cosine similarity + skills gap analysis + seniority fit + location scoring. Pre-computed match scores with full explanations. |
| **AI Resume Tailoring** | LangGraph workflow that customizes your master resume per job posting: keyword injection, bullet reordering, ATS optimization. Fully auditable. |
| **Application Lifecycle Tracking** | Full-cycle tracking from `discovered` → `shortlisted` → `applied` → `offer` with immutable event log. |
| **Email Intelligence** | Gmail integration: classify recruiter emails (9 categories), extract entities (company, role, datetime, meeting link), auto-update application status. |
| **Calendar Automation** | Auto-creates Google Calendar events from interview scheduling emails. Extracts timezone, meeting links, and sets reminders. |
| **Analytics Dashboard** | Funnel analytics, match score distribution, response rate by source, status breakdown, agent run history. |

### Tech Stack

```
Backend:     FastAPI · PostgreSQL 16 · Redis · Celery · LangGraph · pgvector · asyncpg
Frontend:    Next.js 15 · React 18 · TypeScript · Tailwind CSS · shadcn/ui · Framer Motion · TanStack Query
AI/LLM:      OpenAI GPT-4o · Anthropic Claude · LangGraph workflows · text-embedding-3-small
Integrations: Apify · Gmail API · Google Calendar API · Google OAuth
Infra:       Docker · GitHub Actions CI/CD · Vercel (web) · Railway (API) · AWS S3
```

---

## System Design

### Database Schema

The PostgreSQL schema uses **15 normalized tables** with:
- UUID primary keys (server-generated via `uuid-ossp`)
- `pgvector` `vector` columns for semantic embedding search
- Full soft-delete support on users/applications
- Immutable event log (`application_events`) for audit trail
- Deduplication clusters for multi-source job aggregation

### Agent Workflows

Five LangGraph workflows orchestrate the AI layer:

1. **Job Discovery** — Triggers Apify actors, normalizes raw listings, deduplicates, stores embeddings
2. **Job Matching** — Computes embedding similarity + skills overlap + seniority fit per user
3. **Resume Tailoring** — Multi-step: analyze job, identify gaps, rewrite bullets, validate ATS compatibility
4. **Email Intelligence** — Classify → extract entities → update application status → trigger calendar automation
5. **Calendar Automation** — Parse interview datetime/timezone, create Google Calendar event, set reminders

All workflow executions are recorded in `agent_runs` with input/output, model used, tokens consumed, and duration.

---

## Quick Start

### Prerequisites

- Docker + Docker Compose
- Node.js 20+ and pnpm 9+
- Python 3.11+
- Poetry

### First-time setup (recommended)

```bash
git clone https://github.com/sushildalavi/JobSense.git
cd JobSense

# Copy env file and fill in your credentials
cp .env.example .env

# Full dev setup: installs deps, starts infra, runs migrations, seeds demo data
make setup-dev
```

### Start development servers

```bash
# Start everything: frontend, backend, workers, postgres, redis
make dev

# Or start services individually:
make dev-api     # FastAPI on :8000
make dev-web     # Next.js on :3000
make dev-worker  # Celery worker
```

### Access the running services

| Service | URL |
|---|---|
| Next.js Frontend | http://localhost:3000 |
| FastAPI + Swagger | http://localhost:8000/docs |
| Flower (Celery UI) | http://localhost:5555 |
| pgAdmin (optional) | http://localhost:5050 |

Demo credentials (after `make setup-dev`):
- **Email:** `demo@jobsense.dev`
- **Password:** `DemoPass123`

---

## Environment Variables

Copy `.env.example` to `.env` and configure:

| Variable | Description | Required |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string (sync, e.g. `postgresql://user:pass@localhost/db`) | Yes |
| `REDIS_URL` | Redis connection string (e.g. `redis://localhost:6379/0`) | Yes |
| `SECRET_KEY` | JWT signing secret (32+ random characters) | Yes |
| `OPENAI_API_KEY` | OpenAI API key for GPT-4o and embeddings | Yes |
| `ANTHROPIC_API_KEY` | Anthropic API key for Claude | Recommended |
| `APIFY_API_TOKEN` | Apify token for job scraping actors | Yes |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID | For OAuth |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret | For OAuth |
| `GOOGLE_REDIRECT_URI` | OAuth callback URL | For OAuth |
| `AWS_ACCESS_KEY_ID` | AWS access key for S3 file storage | For uploads |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | For uploads |
| `S3_BUCKET_NAME` | S3 bucket for resume/document storage | For uploads |
| `SENTRY_DSN` | Sentry DSN for error tracking | Optional |
| `ENVIRONMENT` | `development` or `production` | Yes |
| `FRONTEND_URL` | Frontend origin for CORS (e.g. `http://localhost:3000`) | Yes |

---

## API Reference

All endpoints live under `/api/v1/`. Interactive documentation at `/docs` (Swagger) and `/redoc`.

### Authentication

| Method | Path | Description |
|---|---|---|
| `POST` | `/auth/register` | Create new account |
| `POST` | `/auth/login` | Login → JWT tokens |
| `POST` | `/auth/refresh` | Refresh access token |
| `GET` | `/auth/me` | Get current user |
| `GET` | `/auth/google` | Initiate Google OAuth |
| `GET` | `/auth/google/callback` | Google OAuth callback |

### Jobs

| Method | Path | Description |
|---|---|---|
| `GET` | `/jobs/` | List jobs with match scores, filters, pagination |
| `GET` | `/jobs/{id}` | Job detail with full description + match breakdown |
| `POST` | `/jobs/{id}/shortlist` | Shortlist a job (creates application) |
| `GET` | `/jobs/search` | Full-text + semantic hybrid search |

### Applications

| Method | Path | Description |
|---|---|---|
| `GET` | `/applications/` | List user's applications |
| `POST` | `/applications/` | Create application for a job |
| `GET` | `/applications/{id}` | Application detail |
| `PATCH` | `/applications/{id}/status` | Transition application status |
| `GET` | `/applications/{id}/events` | Status transition audit log |

### Resume

| Method | Path | Description |
|---|---|---|
| `POST` | `/resumes/upload` | Upload master resume (PDF/DOCX) |
| `GET` | `/resumes/` | List master resumes |
| `POST` | `/resumes/{id}/tailor` | Trigger AI tailoring for a job |
| `GET` | `/resumes/versions/{id}` | Get tailored version |

### Email & Calendar

| Method | Path | Description |
|---|---|---|
| `POST` | `/email/sync` | Trigger Gmail sync |
| `GET` | `/email/threads` | List classified email threads |
| `GET` | `/calendar/events` | List interview calendar events |

### Analytics

| Method | Path | Description |
|---|---|---|
| `GET` | `/analytics/funnel` | Application funnel breakdown |
| `GET` | `/analytics/match-scores` | Match score distribution |
| `GET` | `/analytics/sources` | Response rate by job source |

---

## Project Structure

```
JobSense/
├── apps/
│   ├── api/                      # FastAPI backend
│   │   ├── alembic/              # Database migrations
│   │   │   ├── env.py            # Async Alembic config
│   │   │   └── versions/         # Migration files
│   │   ├── app/
│   │   │   ├── api/              # Route handlers
│   │   │   │   └── v1/routers/   # Versioned API routers
│   │   │   ├── core/             # Config, DB engine, auth utils
│   │   │   ├── models/           # SQLAlchemy ORM models
│   │   │   ├── schemas/          # Pydantic request/response schemas
│   │   │   ├── services/         # Business logic layer
│   │   │   └── workers/          # Celery tasks (5 queues)
│   │   ├── scripts/
│   │   │   └── seed.py           # Demo data seeder
│   │   ├── tests/
│   │   │   ├── conftest.py       # Shared pytest fixtures
│   │   │   ├── test_auth.py      # Auth endpoint tests
│   │   │   ├── test_jobs.py      # Jobs endpoint tests
│   │   │   └── test_applications.py
│   │   ├── alembic.ini
│   │   ├── main.py               # FastAPI app factory
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   └── web/                      # Next.js 15 frontend
│       ├── app/                  # App Router pages
│       ├── components/           # React components + shadcn/ui
│       ├── lib/                  # API client, utilities
│       └── Dockerfile
├── packages/
│   ├── types/                    # Shared TypeScript types
│   ├── shared/                   # Shared utilities
│   ├── agent/                    # LangGraph agent workflows
│   └── integrations/             # Apify, Gmail, Calendar connectors
├── docker/
│   └── postgres/
│       └── init.sql              # Extensions + grants
├── .github/
│   └── workflows/
│       ├── ci.yml                # Test + lint on every PR
│       └── deploy.yml            # Deploy to Railway + Vercel on main
├── docker-compose.yml            # Production-like local stack
├── docker-compose.override.yml   # Dev overrides (hot-reload + volume mounts)
├── Makefile                      # All developer commands
├── package.json                  # pnpm workspace root
├── pnpm-workspace.yaml
└── turbo.json                    # Turborepo pipeline config
```

---

## Development Workflow

```bash
# Run the full test suite
make test

# Run only API tests
make test-api

# Run only frontend tests
make test-web

# Lint everything
make lint

# Format (black + isort on Python, prettier on TypeScript)
make format

# Type check (mypy + tsc)
make type-check

# Create a new migration
make migrate-create name="add_user_preferences"

# Apply all pending migrations
make migrate

# Roll back one migration
make migrate-down

# Reseed demo data
make seed

# Full reset (DANGER: drops and recreates all data)
make db-reset
```

---

## Roadmap

### MVP (Current)

- [x] Monorepo scaffold (Next.js + FastAPI + Turborepo)
- [x] Full database schema with migrations (Alembic + pgvector)
- [x] User auth (JWT + Google OAuth)
- [x] Job ingestion pipeline (Apify actors)
- [x] Semantic job matching (pgvector + skills scoring)
- [x] Resume upload + parsing (PDF/DOCX)
- [x] AI resume tailoring (LangGraph + GPT-4o)
- [x] Application lifecycle tracking (full audit trail)
- [x] Email intelligence (Gmail + entity extraction)
- [x] Calendar automation (Google Calendar)
- [x] Analytics dashboard
- [x] CI/CD (GitHub Actions → Railway + Vercel)
- [x] Docker Compose development stack

### V2 — Automation

- [ ] Browser automation with Playwright (auto form-fill on application portals)
- [ ] Multi-agent job discovery loop (autonomous search + ranking)
- [ ] Cover letter generation (per-job, personalized, truthful)
- [ ] Follow-up email drafting agent (context-aware)
- [ ] Job market analytics (salary benchmarking by role + location)
- [ ] LinkedIn profile sync (import skills, experience)
- [ ] Team / shared workspace support (recruiters + candidates)

### V3 — Platform

- [ ] Mobile app (React Native / Expo)
- [ ] Real-time notifications (WebSockets + push)
- [ ] Interview prep agent (mock interviews, feedback)
- [ ] Offer negotiation assistant (comp benchmarking + counter-offer drafts)
- [ ] Recruiter relationship CRM (contact tracking, follow-up reminders)
- [ ] Multi-user SaaS with billing (Stripe + usage tiers)
- [ ] Plugin marketplace (ATS connectors, job board integrations)

---

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository and create a feature branch: `git checkout -b feat/my-feature`
2. Make your changes with tests and docstrings
3. Run `make lint && make test` to verify everything passes
4. Open a pull request against `main` with a clear description

For large features, please open an issue first to discuss the approach.

### Code Style

- **Python:** [ruff](https://docs.astral.sh/ruff/) for linting + formatting, [mypy](https://mypy-lang.org/) for type checking
- **TypeScript:** ESLint + Prettier (configured via `pnpm lint` / `pnpm format`)
- **Commits:** Conventional Commits format (`feat:`, `fix:`, `docs:`, `chore:`)

---

## License

[MIT](LICENSE) — built by [Sushil Dalavi](https://github.com/sushildalavi).
