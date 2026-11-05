# DevPilot

DevPilot is a FastAPI service backed by PostgreSQL. It is an early project skeleton: configuration, a database session, Alembic migrations, health checks, tests, and CI are in place so new features can be added on a consistent base.

## Requirements

- Python 3.12 or newer
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Docker, for the local PostgreSQL service
- Git

## Clone

```bash
git clone https://github.com/awoladhossain/Devpilot.git
cd Devpilot
```

SSH works the same way if your key is already set up:

```bash
git clone git@github.com:awoladhossain/Devpilot.git
cd Devpilot
```

## Setup

Install the locked dependencies, including the dev group (pytest, Ruff, pre-commit):

```bash
uv sync --locked
```

Copy the example environment file:

```bash
cp .env.example .env
```

Start PostgreSQL:

```bash
docker compose up -d
```

Compose publishes Postgres on the host at `127.0.0.1:5435`, and `.env.example` uses that port. CI runs Postgres on `5432` and does not read `.env`; the fallback URL in `app/core/config.py` matches CI.

Apply migrations:

```bash
uv run alembic upgrade head
```

Optional: install the pre-commit hook so Ruff checks and formats files before each commit:

```bash
uv run pre-commit install
```

## Run

```bash
uv run fastapi dev
```

The API is served at [http://127.0.0.1:8000](http://127.0.0.1:8000). Interactive docs are at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

`fastapi dev` reloads on file changes. For a production-style process without reload:

```bash
uv run fastapi run
```

## API

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Process is up. Returns `{"status": "ok"}`. |
| `GET` | `/health/db` | Database accepts a query. HTTP 200 `{"status": "ok"}`, or HTTP 503 `{"status": "error"}` when the query fails. |

Quick check after the server is running:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/health/db
```

## Configuration

Settings are loaded from the environment and from `.env`. See `app/core/config.py` and `.env.example`.

| Variable | Default | Used by |
|---|---|---|
| `APP_ENV` | `local` | Application |
| `LOG_LEVEL` | `INFO` | Application |
| `DATABASE_URL` | `postgresql+psycopg://devpilot:devpilot@localhost:5432/devpilot` | Application and Alembic. `.env.example` uses port `5435` for local Compose. |
| `POSTGRES_USER` | `devpilot` | Docker Compose |
| `POSTGRES_PASSWORD` | `devpilot` | Docker Compose |
| `POSTGRES_DB` | `devpilot` | Docker Compose |

`.env` is gitignored. Do not commit real credentials.

## Database

PostgreSQL 17 runs from `compose.yaml`. Data is stored in the `pgdata` volume.

```bash
docker compose up -d      # start
docker compose ps         # status
docker compose logs db    # logs
docker compose down       # stop, keep data
docker compose down -v    # stop and delete the volume
```

Alembic lives in `migrations/` and reads `DATABASE_URL` from settings. The current revision is an empty baseline.

```bash
uv run alembic upgrade head    # apply pending migrations
uv run alembic current         # show the applied revision
uv run alembic history         # list revisions
```

After you add or change a SQLAlchemy model that uses `Base` in `app/db/base.py`:

```bash
uv run alembic revision --autogenerate -m "describe the change"
uv run alembic upgrade head
```

Review the generated file before applying it. Autogenerate does not catch every change.

## Test

The health-database test needs Postgres running and `DATABASE_URL` pointing at it. Apply migrations first.

```bash
uv run pytest
```

Run a single file or test:

```bash
uv run pytest tests/test_health.py
uv run pytest tests/test_health.py::test_health_db_ok
```

Tests that need a database are marked `integration`:

```bash
uv run pytest -m integration
```

## Lint and format

Ruff is the linter and formatter. Line length is 100. Migrations are excluded.

```bash
uv run ruff check .
uv run ruff format --check .
```

Apply fixes and rewrite formatting:

```bash
uv run ruff check . --fix
uv run ruff format .
```

## Project layout

```text
app/
  main.py              FastAPI application
  api/health.py        Health routes
  core/config.py       Settings
  db/base.py           SQLAlchemy base and naming convention
  db/session.py        Engine and session dependency
migrations/            Alembic environment and revisions
tests/                 Pytest tests
docs/GITHUB_WORKFLOW.md
.github/workflows/ci.yml
compose.yaml           Local PostgreSQL
pyproject.toml         Project metadata, dependencies, Ruff, Pytest
alembic.ini
.env.example
```

## Continuous integration

On every pull request and on pushes to `main`, GitHub Actions runs:

1. `uv sync --locked`
2. `uv run ruff check .`
3. `uv run ruff format --check .`
4. `uv run alembic upgrade head` against a Postgres 17 service
5. `uv run pytest`

Run the same commands locally before opening a pull request. Git, pull request, and squash-merge notes are in [docs/GITHUB_WORKFLOW.md](docs/GITHUB_WORKFLOW.md).
