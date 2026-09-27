# Product Availability Monitoring Platform

Monitor product price and stock changes on e-commerce sites and get notified when something changes. Built for personal, multi-user tracking with per-account isolation, configurable email and ntfy notifications, and a pluggable adapter architecture. **HMT Watches** (`hmtwatches.in`) is supported today; additional sites (Titan, Casio, Seiko, etc.) can be added by implementing a new adapter class — no changes to core polling, auth, or notification logic required.

## Features

- **Multi-user accounts** — JWT signup/login, each user tracks their own products
- **Product monitoring** — poll tracked URLs on a configurable interval (default 15 min)
- **Change detection** — price changes, back-in-stock, out-of-stock, and new model events with history
- **Notifications** — per-user rich HTML email (via Resend) and/or [ntfy](https://ntfy.sh) mobile push notifications; console fallback
- **Idempotent Dispatch** — database-backed event logging (`NotificationLog`) prevents duplicate notifications across retries or parallel workers
- **5-Phase Polling Pipeline** — structured 5-phase background execution (Catalog Sync, Dual-Source Product Discovery, Change Detection, Event Generation, Notification Dispatch)
- **Dual HMT Sources** — full product discovery from both `hmtwatches.in` and `hmtwatches.store`
- **Email verification** — prevents adding someone else's address as a notification target
- **Abuse protection** — signup rate limits, per-user product caps, account deletion
- **Extensible adapters** — add new sites by subclassing `SiteAdapter` (see below)
- **Production-ready** — SQLite for local dev, Postgres for deployment ([DEPLOY.md](DEPLOY.md))

## Quickstart (local dev)

**Requirements:** Python 3.12+

```bash
git clone https://github.com/YOUR_ORG/product-availability-monitor.git
cd product-availability-monitor

python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env — set JWT_SECRET to a random string (e.g. openssl rand -hex 32)

uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Health check:

```bash
curl http://localhost:8000/health
```

### Sign up and track a product

```bash
# Sign up
curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"your-secure-password"}'

export TOKEN="<access_token from response>"

# Track a product (paste a real product_overview URL from hmtwatches.in)
curl -X POST http://localhost:8000/products \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"url":"https://hmtwatches.in/product_overview?id=YOUR_PRODUCT_ID"}'

# List your products
curl http://localhost:8000/products -H "Authorization: Bearer $TOKEN"
```

See [DEPLOY.md](DEPLOY.md) for production deployment on Railway with Postgres.

## Architecture

The app is a single FastAPI process that also runs an APScheduler background job executing a robust **5-phase polling pipeline**:

1. **Catalog Synchronization** — ingest catalog changes & sync master reference models.
2. **Product Discovery** — fetch active product listings from both `hmtwatches.in` and `hmtwatches.store` with URL deduplication.
3. **Change Detection** — evaluate price updates, back-in-stock, out-of-stock, and new model events.
4. **Event Generation** — construct strongly-typed `NotificationEvent` payloads with product details.
5. **Notification Dispatch** — deliver alerts idempotently to users via registered channels (Email, ntfy).

| Directory | Purpose |
|-----------|---------|
| `adapters/` | `SiteAdapter` implementations + domain registry |
| `api/` | FastAPI routes (auth, products, notifications, account) |
| `catalog/` | Catalog model sync and management |
| `core/` | Change detection, JWT/password helpers |
| `db/` | SQLAlchemy models, migration scripts, and database session |
| `events/` | Core notification event models (`NotificationEvent`) |
| `notifications/` | Dispatcher + email (rich HTML), ntfy (topics/backoff retry), console channels |
| `scheduler/` | APScheduler background polling jobs |
| `services/` | Polling pipeline orchestration (`PollingPipeline`) |
| `tests/` | Comprehensive pytest suite & E2E production validation |
| `fixtures/` | Offline HTML samples for adapter tests |

## Adding a new site adapter

1. **Subclass `SiteAdapter`** in `adapters/base.py`:
   - `site_name` — short identifier (e.g. `"hmt"`)
   - `fetch_product(url)` — HTTP fetch + parse → `ProductSnapshot`
   - `parse_html(url, html)` — optional but recommended for offline testing

2. **Implement the adapter** — see `adapters/hmt.py` as the reference:
   - Parse server-rendered HTML with BeautifulSoup
   - Return `ProductSnapshot(url, title, price, in_stock, raw={...})`
   - Validate URLs with an `is_supported_url()` helper

3. **Register in `adapters/registry.py`:**
   ```python
   if domain.endswith("example.com"):
       return ExampleAdapter()
   ```

4. **Add tests** with a saved HTML fixture under `fixtures/`.

No changes needed in API routes, scheduler, or change detection.

## Configuration

Copy `.env.example` to `.env`. Key variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `JWT_SECRET` | *(required)* | Secret for JWT signing |
| `DATABASE_URL` | SQLite path | Postgres URL in production |
| `BASE_URL` | `http://localhost:8000` | Public URL for email verification links |
| `POLL_INTERVAL_SECONDS` | `900` | How often to poll products |
| `MAX_PRODUCTS_PER_USER` | `20` | Product cap per account |
| `RESEND_API_KEY` | *(empty)* | Resend API key for email |
| `RESEND_FROM_EMAIL` | *(empty)* | Verified sender in Resend |
| `NTFY_SERVER_URL` | `https://ntfy.sh` | ntfy server URL for push notifications |
| `NTFY_MAX_RETRIES` | `3` | Retries for transient ntfy failures |
| `NTFY_RETRY_BACKOFF_SECONDS` | `2.0` | Initial exponential backoff delay for ntfy retries |

Full list in `.env.example`.

## API overview

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | No | Health check |
| POST | `/auth/signup` | No | Create account |
| POST | `/auth/login` | No | Log in |
| DELETE | `/account` | JWT | Delete account and all data |
| POST/GET/DELETE | `/notification-preferences` | JWT | Manage notification channels |
| GET | `/notification-preferences/verify` | No | Verify email preference |
| POST/GET/DELETE | `/products` | JWT | Track and manage products |
| GET | `/products/{id}/history` | JWT | Snapshot and change history |

## Tests

```bash
pytest -v
```

Offline HMT parsing tests use `fixtures/hmt_product_sample.html`.

## Deployment

See **[DEPLOY.md](DEPLOY.md)** for Railway + Postgres setup.

## Legal & Ethical Use

This tool is intended for **personal monitoring** of products you care about — tracking prices and availability for your own use.

- It fetches **publicly available** product pages using plain HTTP requests at **reasonable polling intervals** (default 15 minutes).
- It does **not** bypass login walls, CAPTCHAs, or other access controls.
- **You are responsible** for complying with each target site's terms of service and applicable laws in your jurisdiction.
- This project makes **no legal claims** about whether scraping a given site is permitted; use your own judgment and respect site policies.

Do not use this software to harass sites with aggressive polling, circumvent technical protections, or monitor products at a scale that could harm the target infrastructure.

## Contributing

Contributions are welcome — especially new site adapters! See [CONTRIBUTING.md](CONTRIBUTING.md).

## Security

To report a vulnerability privately, see [SECURITY.md](SECURITY.md).

## License

MIT License — see [LICENSE](LICENSE). Copyright (c) 2026 [Your Name] — replace with your name before publishing.
