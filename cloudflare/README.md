# HMT Notification System — Cloudflare Architecture ($0/Month)

This directory contains the complete production Cloudflare architecture for the HMT Watch Notification System.

## Architecture

- **Cloudflare Worker**: TypeScript engine (`src/index.ts`) handling cron triggers and API endpoints.
- **Cloudflare Cron Trigger**: `*/2 * * * *` (2-minute interval) replacing APScheduler.
- **Cloudflare D1 Database**: Native SQLite database (`migrations/0001_initial.sql`) storing catalog products, snapshots, change events, and notification logs.
- **Cloudflare Workers Static Assets**: Serves the React 19 + Vite frontend SPA from `../frontend/dist`.
- **Resend**: Transactional HTML email alerts.
- **ntfy**: Instant mobile push notifications with one-tap deep links to HMT.

## Local Development & Setup

1. **Install Dependencies**:
   ```bash
   cd cloudflare
   npm install
   ```

2. **Run Local Worker Dev Server**:
   ```bash
   npm run dev
   ```

3. **Run Unit Tests**:
   ```bash
   npm test
   ```

4. **Type Check**:
   ```bash
   npm run typecheck
   ```

5. **Apply Local D1 Migrations**:
   ```bash
   npx wrangler d1 migrations apply hmt-db --local
   ```

## Production Deployment

1. **Create D1 Database**:
   ```bash
   npx wrangler d1 create hmt-db
   ```
   Update `wrangler.json` with your returned `database_id`.

2. **Apply Production Migrations**:
   ```bash
   npx wrangler d1 migrations apply hmt-db --remote
   ```

3. **Configure Worker Secrets**:
   ```bash
   npx wrangler secret put RESEND_API_KEY
   npx wrangler secret put RESEND_TO_EMAIL
   npx wrangler secret put RESEND_FROM_EMAIL
   npx wrangler secret put NTFY_TOPIC
   ```

4. **Build Frontend**:
   ```bash
   cd ../frontend
   npm run build
   cd ../cloudflare
   ```

5. **Deploy Worker & Assets**:
   ```bash
   npx wrangler deploy
   ```

## Idempotency Guarantee

Notifications enforce strict uniqueness via D1 constraint `UNIQUE(event_id, channel_type, destination, user_id)`. Every alert is sent **EXACTLY ONCE** per stock transition event.
