# Recruiter Market Brief (RMB)

Phase 1 implementation of the Recruiter Market Brief data pipeline, Supabase-backed storage, and minimal UI.

## Quick Start

1.  Clone the repo:
    ```bash
    git clone https://github.com/MAM1967/RMB.git
    cd RMB
    ```
2.  Create and populate a `.env` file:
    ```bash
    cp .env.example .env
    # Edit .env with your Supabase and Apify credentials
    ```
3.  Set up the Python backend (using Poetry):
    ```bash
    poetry install
    poetry run pre-commit install
    poetry run pytest
    ```
4.  Run the backend scripts:
    ```bash
    poetry run python scripts/run_daily_scrape.py --company=stripe
    poetry run python scripts/compute_metrics.py
    ```
5.  Run the frontend:
    ```bash
    cd frontend
    npm install
    npm run dev
    ```

## Architecture

The system is a monorepo with:

- `backend/` – Python data pipeline (scrapers, processors, metrics, API).
- `database/` – Supabase/Postgres schema and migrations.
- `config/` – JSON configuration for companies and taxonomies.
- `frontend/` – Minimal web UI for viewing the brief and metrics.
- `scripts/` – Operational entrypoints (daily scrape, metrics).
- `tests/` – Unit and integration tests.

See `docs/architecture.md` for the high-level data flow.

## Development

- Python 3.11+
- Poetry for dependency management
- Node.js 20+ for the frontend

Recommended workflow:

- Create feature branches from `main`.
- Run `ruff`, `black`, `mypy`, and `pytest` locally before pushing.
- Keep `cursorrules.mdc` and `recruiter_market_brief_prd_v1.md` in sync with behavior.

## Deployment

- Supabase hosts the Postgres database and (optionally) auth.
- GitHub Actions run CI, the daily scrape, and weekly metrics jobs.
- GitHub Secrets provide Supabase and Apify credentials to workflows.

For details on database setup and migrations, see `database/schema.sql` and `database/migrations/`.
