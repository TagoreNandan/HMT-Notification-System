# Contributing

Thank you for your interest in contributing to the Product Availability Monitoring Platform!

## Development setup

1. **Prerequisites:** Python 3.12+

2. **Clone and install:**
   ```bash
   git clone https://github.com/YOUR_ORG/product-availability-monitor.git
   cd product-availability-monitor
   python3.12 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env — at minimum set JWT_SECRET to a random string for local dev
   ```

4. **Run the API locally:**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Run tests:**
   ```bash
   pytest -v
   ```

Tests use in-memory SQLite and do not require Postgres, Resend, or network access for the adapter parsing tests (offline HTML fixture).

## Branch and pull request conventions

- Branch from `main` using descriptive names: `feature/titan-adapter`, `fix/email-verify-expiry`, etc.
- Keep PRs focused — one logical change per PR when possible.
- Include tests for new behavior where applicable.
- Ensure `pytest` passes before opening a PR.
- Describe what changed and why in the PR body.

## Code style

- Match existing patterns in the codebase (type hints, Pydantic models, SQLAlchemy 2.0 style).
- Keep changes minimal and scoped — avoid unrelated refactors in the same PR.
- No secrets in code, tests, or committed config files.

## Site adapters — especially welcome!

Adding support for new e-commerce sites is one of the highest-value contributions. To add a site:

1. Create `adapters/your_site.py` implementing `SiteAdapter` from `adapters/base.py`.
2. Implement `site_name`, `fetch_product()`, and (for testability) `parse_html()`.
3. Register the adapter in `adapters/registry.py` keyed by domain.
4. Add a test fixture HTML file under `fixtures/` and parsing tests in `tests/`.

Use `adapters/hmt.py` as the reference implementation.

## Questions

Open a GitHub Discussion or issue for design questions before large changes. For security issues, see [SECURITY.md](SECURITY.md) — do not file public issues for vulnerabilities.
