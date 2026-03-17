# ApplyFlow — Deployment Guide

This guide deploys:
- **Frontend** → [Vercel](https://vercel.com) (free tier)
- **Backend API + Workers** → [Railway](https://railway.app) (~$5/mo or free trial)
- **PostgreSQL + Redis** → Railway (included with above)

---

## Prerequisites

- GitHub account (repo already pushed)
- [Vercel account](https://vercel.com/signup) — sign up with GitHub
- [Railway account](https://railway.app) — sign up with GitHub

---

## Step 1 — Deploy the Database on Railway

1. Go to [railway.app/new](https://railway.app/new)
2. Click **"Deploy PostgreSQL"** → Railway creates a managed Postgres instance
3. Click the PostgreSQL service → **"Variables"** tab → copy `DATABASE_URL`
4. From the same project, click **"+ New Service"** → **"Deploy Redis"**
5. Copy the Redis `REDIS_URL` from its Variables tab

> **Enable pgvector extension:**
> In Railway's PostgreSQL service → **"Query"** tab, run:
> ```sql
> CREATE EXTENSION IF NOT EXISTS vector;
> CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
> CREATE EXTENSION IF NOT EXISTS pg_trgm;
> ```

---

## Step 2 — Deploy the API on Railway

1. In the same Railway project, click **"+ New Service"** → **"GitHub Repo"**
2. Connect your repo → select `ApplyFlow`
3. **Root directory:** `apps/api`
4. Railway auto-detects `railway.toml` — no extra config needed
5. Add these **environment variables** in the service's Variables tab:

| Variable | Value |
|---|---|
| `DATABASE_URL` | From Step 1 |
| `REDIS_URL` | From Step 1 |
| `SECRET_KEY` | Any random 64-char string (run: `openssl rand -hex 32`) |
| `OPENAI_API_KEY` | `sk-...` from platform.openai.com |
| `ANTHROPIC_API_KEY` | `sk-ant-...` from console.anthropic.com |
| `DEFAULT_LLM_PROVIDER` | `openai` |
| `APIFY_API_TOKEN` | From apify.com/account |
| `GOOGLE_CLIENT_ID` | From Google Cloud Console |
| `GOOGLE_CLIENT_SECRET` | From Google Cloud Console |
| `GOOGLE_REDIRECT_URI` | `https://YOUR-RAILWAY-DOMAIN.railway.app/api/v1/auth/google/callback` |
| `ENVIRONMENT` | `production` |
| `LOG_LEVEL` | `INFO` |
| `FRONTEND_URL` | `https://YOUR-VERCEL-DOMAIN.vercel.app` (set after Step 3) |

6. Click **Deploy** — Railway builds and starts the API
7. Copy your Railway API domain (e.g. `applyflow-api-production.up.railway.app`)

---

## Step 3 — Deploy the Worker on Railway

1. In the same Railway project, click **"+ New Service"** → **"GitHub Repo"** again
2. Same repo, same root directory `apps/api`
3. **Override the start command** in Settings → Deploy:
   ```
   celery -A app.tasks.celery_app.celery_app worker --loglevel=info -Q ingestion,matching,ai,email,calendar,default --concurrency=2
   ```
4. Add the **same environment variables** as Step 2
5. Name this service `applyflow-worker`

---

## Step 4 — Deploy the Frontend on Vercel

1. Go to [vercel.com/new](https://vercel.com/new)
2. Import your GitHub repo
3. **Framework:** Next.js (auto-detected)
4. **Root Directory:** `apps/web`
5. **Build Command:** (leave default — Vercel reads `vercel.json`)
6. Add these **environment variables**:

| Variable | Value |
|---|---|
| `NEXT_PUBLIC_API_URL` | `https://YOUR-RAILWAY-DOMAIN.railway.app/api/v1` |
| `NEXT_PUBLIC_APP_URL` | `https://YOUR-VERCEL-DOMAIN.vercel.app` |
| `NEXT_PUBLIC_POSTHOG_KEY` | Optional — from posthog.com |

7. Click **Deploy**
8. Copy your Vercel domain → go back to Railway and update `FRONTEND_URL`

---

## Step 5 — Run Migrations

After the API is deployed, run migrations once:

```bash
# Option A: via Railway CLI (install with: npm i -g @railway/cli)
railway login
railway link   # select your project
cd apps/api
railway run alembic upgrade head

# Option B: via Railway dashboard
# API service → "Shell" tab → run: alembic upgrade head
```

---

## Step 6 — Set Up GitHub Actions (CI/CD)

Add these secrets to your GitHub repo:
**Settings → Secrets and variables → Actions → New repository secret**

| Secret | How to get it |
|---|---|
| `RAILWAY_TOKEN` | Railway dashboard → Account → Tokens → Create |
| `DATABASE_URL` | From Railway PostgreSQL service |
| `VERCEL_TOKEN` | vercel.com/account/settings/tokens → Create |
| `VERCEL_ORG_ID` | Run `vercel whoami` or check `.vercel/project.json` after first deploy |
| `VERCEL_PROJECT_ID` | Check `.vercel/project.json` after first deploy |
| `NEXT_PUBLIC_API_URL` | Your Railway API URL |
| `NEXT_PUBLIC_APP_URL` | Your Vercel URL |

After this, every push to `main` automatically:
1. Runs CI (tests + lint)
2. Deploys API + workers to Railway
3. Runs migrations
4. Deploys frontend to Vercel

---

## Step 7 — Google OAuth Setup

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a new project → **"APIs & Services"** → **"Credentials"**
3. **"Create Credentials"** → **"OAuth 2.0 Client IDs"**
4. Application type: **Web application**
5. Authorized redirect URIs:
   - `https://YOUR-RAILWAY-DOMAIN.railway.app/api/v1/auth/google/callback`
   - `http://localhost:8000/api/v1/auth/google/callback` (for local dev)
6. Enable these APIs: **Gmail API**, **Google Calendar API**
7. Copy Client ID and Client Secret → add to Railway env vars

---

## Verify Everything Works

```bash
# API health check
curl https://YOUR-RAILWAY-DOMAIN.railway.app/health

# API docs
open https://YOUR-RAILWAY-DOMAIN.railway.app/docs

# Frontend
open https://YOUR-VERCEL-DOMAIN.vercel.app
```

---

## Quick Reference: All URLs

| Service | URL |
|---|---|
| Frontend | `https://YOUR-PROJECT.vercel.app` |
| API | `https://YOUR-PROJECT.up.railway.app` |
| API Docs | `https://YOUR-PROJECT.up.railway.app/docs` |
| Health Check | `https://YOUR-PROJECT.up.railway.app/health` |

---

## Troubleshooting

**Build fails on Vercel (monorepo not found)**
→ Ensure Root Directory is set to `apps/web` in Vercel project settings

**API crashes on Railway (import errors)**
→ Check that all env vars are set, especially `DATABASE_URL` and `SECRET_KEY`

**Migrations fail**
→ Make sure pgvector extension is enabled (Step 1) before running `alembic upgrade head`

**CORS errors in browser**
→ Set `FRONTEND_URL` in Railway to your exact Vercel URL (no trailing slash)

**Google OAuth redirect mismatch**
→ The `GOOGLE_REDIRECT_URI` env var must exactly match what's registered in Google Console
