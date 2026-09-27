# Cloudflare Production Deployment & Operations Guide

## Overview

The HMT Notification System operates on a **$0/month Cloudflare Serverless Architecture**.

## Production Topology

- **Worker Name**: `hmt-watch-monitor`
- **Cron Schedule**: `*/2 * * * *` (Every 120 seconds)
- **Database**: Cloudflare D1 (`hmt-db`)
- **Frontend SPA**: React 19 / Vite hosted via Workers Static Assets at `/`
- **Backend REST API**: Served at `/api/*` and `/health`

## Environment & Secrets Checklist

| Variable / Secret | Description | Where Configured |
|---|---|---|
| `DB` | D1 Database Binding | `wrangler.json` |
| `ASSETS` | Frontend Dist Assets Binding | `wrangler.json` |
| `RESEND_API_KEY` | Resend HTTP API Key | Cloudflare Secret |
| `RESEND_TO_EMAIL` | Alert recipient email address | Cloudflare Secret |
| `RESEND_FROM_EMAIL` | Verified sender domain | Cloudflare Secret |
| `NTFY_TOPIC` | Private ntfy mobile push topic | Cloudflare Secret |
| `NTFY_SERVER_URL` | Push server URL (`https://ntfy.sh`) | Cloudflare Secret / Env |

## Rollback Procedure

If you ever need to fall back to the Python/FastAPI backend:
1. The Python/FastAPI codebase remains 100% intact at commit `23e6ad1`.
2. Start the local/Railway backend via `uvicorn main:app --host 0.0.0.0 --port 8000`.
3. Start the scheduler via `python -m scheduler`.
