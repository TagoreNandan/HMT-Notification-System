# Deploying to Railway

This guide walks through deploying the Product Availability Monitor as a single 24/7 instance on [Railway](https://railway.app), backed by Postgres.

## Architecture on Railway

- **One web service** runs FastAPI + APScheduler in the same process (`--workers 1`).
- **One Postgres database** stores all data (replaces local SQLite).
- **No separate worker** — the scheduler polls products inside the web process.

> **Important:** Always run with a **single uvicorn worker**. Multiple workers would start multiple APScheduler instances and duplicate poll jobs. The `Procfile`, `railway.json`, and `Dockerfile` all enforce `--workers 1`.

## Prerequisites

- GitHub account with this repo pushed
- Railway account (free tier works to start)
- Resend account (optional, for email notifications)

---

## Step 1: Create a Railway account and project

1. Go to [railway.app](https://railway.app) and sign up (GitHub login is easiest).
2. Click **New Project**.
3. Choose **Deploy from GitHub repo** and authorize Railway to access your GitHub account.
4. Select the repository containing this project.

Railway will create a service and attempt a first deploy. It may fail until Postgres and env vars are configured — that's expected.

---

## Step 2: Add Postgres

1. Inside your Railway project, click **+ New**.
2. Select **Database → PostgreSQL**.
3. Wait for the database to provision (usually under a minute).
4. Click the **Postgres** service, open the **Variables** or **Connect** tab.
5. Copy the **`DATABASE_URL`** value (Railway provides `postgresql://...` or `postgres://...`; both work).

---

## Step 3: Configure the web service environment variables

1. Click your **web service** (the one deployed from GitHub, not Postgres).
2. Open **Variables**.
3. Add the following (adjust values as needed):

| Variable | Example / notes |
|----------|-----------------|
| `DATABASE_URL` | Paste from Postgres service (or use Railway's **Reference Variable** to link `${{Postgres.DATABASE_URL}}`) |
| `JWT_SECRET` | Long random string (e.g. `openssl rand -hex 32`) |
| `BASE_URL` | Your public Railway URL, e.g. `https://your-app.up.railway.app` |
| `RESEND_API_KEY` | From [resend.com](https://resend.com) (optional) |
| `RESEND_FROM_EMAIL` | Verified sender in Resend (optional) |
| `POLL_INTERVAL_SECONDS` | `900` (15 min) or `1800` for production |
| `MAX_PRODUCTS_PER_USER` | `20` |
| `SIGNUP_RATE_LIMIT` | `5/hour` |
| `NOTIFICATION_PREFERENCE_RATE_LIMIT` | `20/hour` |
| `EMAIL_VERIFICATION_EXPIRE_HOURS` | `24` |

Railway automatically sets **`PORT`** — do not override it.

4. Click **Deploy** or wait for auto-redeploy after saving variables.

---

## Step 4: Set the public domain (BASE_URL)

1. On the web service, open **Settings → Networking**.
2. Click **Generate Domain** to get a `*.up.railway.app` URL.
3. Copy that URL into the `BASE_URL` env var (with `https://`).
4. Redeploy if needed so verification email links use the correct host.

---

## Step 5: Verify the deployment

### Health check

```bash
curl https://your-app.up.railway.app/health
```

Expected: `{"status":"ok","app":"Product Availability Monitor"}`

### Check logs for scheduler

1. In Railway, open your **web service**.
2. Click **Deployments → View Logs** (or the **Logs** tab).
3. Look for lines like:

```
INFO [main] Database URL scheme: postgresql
INFO [scheduler] Scheduler started; polling every 900 seconds
INFO [scheduler] Poll job completed for N active product(s)
```

Tables are created automatically on startup via `init_db()` → `create_all()`. No manual migration step is required for a fresh Postgres database.

### Optional: manual init script

If you ever need to initialize tables without starting the web server:

```bash
railway run python scripts/init_db.py
```

This is idempotent — safe to run multiple times.

---

## Step 6: Connect GitHub for auto-deploy

If not already connected:

1. Web service → **Settings → Source**.
2. Connect the GitHub repo and branch (usually `main`).
3. Enable **Auto Deploy** on push.

Every push to the connected branch triggers a new Railway deployment.

---

## Local development (unchanged)

Local dev still uses SQLite by default when `DATABASE_URL` is unset or points to SQLite:

```bash
cp .env.example .env
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Tests always use in-memory SQLite — no Postgres required to run `pytest`.

### Optional: test against local Postgres via Docker

```bash
docker run -d --name hmt-postgres \
  -e POSTGRES_USER=monitor \
  -e POSTGRES_PASSWORD=monitor \
  -e POSTGRES_DB=monitor \
  -p 5433:5432 postgres:16

export DATABASE_URL=postgresql://monitor:monitor@localhost:5433/monitor
python scripts/init_db.py
uvicorn main:app --host 0.0.0.0 --port 8000
```

Or use the included compose file:

```bash
docker compose -f docker-compose.postgres.yml up --build
```

---

## Troubleshooting

| Symptom | Likely cause |
|---------|--------------|
| App crashes on startup | Missing `DATABASE_URL` or invalid Postgres credentials |
| `ModuleNotFoundError: psycopg2` | Redeploy after pulling latest `requirements.txt` |
| Duplicate poll jobs | More than one uvicorn worker — ensure `--workers 1` |
| Email verification links broken | `BASE_URL` not set to public Railway HTTPS URL |
| Scheduler not polling | Check logs; confirm service is running (not sleeping on free tier limits) |

---

## Why single instance?

This MVP uses APScheduler's in-memory job store. That is correct for one Railway replica. Do not scale to multiple instances without adding a shared job store (out of scope for this phase).
