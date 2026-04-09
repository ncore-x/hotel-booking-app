# CLAUDE.md

## Stack

**Backend:** Python 3.12, FastAPI, SQLAlchemy, Alembic, PostgreSQL, Redis, Celery  
**Frontend:** React 19, TypeScript 5.9, Vite 8, Tailwind CSS v4, Zustand v5  
**Package managers:** `uv` (backend), `npm` (frontend)

## Commands

```bash
# Backend
uv run uvicorn src.main:app --reload
uv run pytest tests/
uv run ruff format src/ tests/ && uv run ruff check src/ tests/
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "description"
uv run celery -A src.tasks.celery_app:celery_instance worker --loglevel=info

# Frontend (port 5173, proxies /api → localhost:7777)
cd frontend && npm run dev
cd frontend && npm run build

# Docker (CI stack only)
docker compose -f docker-compose-ci.yml up -d
```

## Skills

- `/go` — orchestrator, use before any non-trivial task
- `/pre-commit` — manual lint + format check
- `/new-endpoint` — step-by-step guide for adding a new endpoint
- `/fix-bugs` — list of known bugs with exact locations and fixes
- `/migrate` — Alembic migration workflow

## Agents

Agents are in `.claude/agents/`. They load automatically — no manual invocation needed.

## Rules

- `.claude/rules/coding.md` — coding standards, architecture constraints
- `.claude/rules/git.md` — git workflow, commit rules

## Detailed Docs

- `.claude/docs/architecture.md` — backend layers, DBManager, auth, RBAC, caching, exceptions, endpoints
- `.claude/docs/frontend.md` — React conventions, i18n, design tokens, known issues
- `.claude/docs/testing.md` — test environment setup, common failure causes
- `.claude/docs/observability.md` — Prometheus, Grafana, Loki, Tempo, alerting, exporters
- `.claude/docs/deployment.md` — Docker, CI/CD, nginx, production settings, SSH tunnels
- `.claude/docs/planned.md` — planned features (location field split), known missing features

## Developer Docs (for humans)

- `docs/DEVELOPER_GUIDE.md` — index page linking to all developer docs
- `docs/getting-started.md` — quick start, install, run
- `docs/architecture.md` — layers, project structure, models, schemas, code patterns
- `docs/api.md` — all HTTP endpoints reference
- `docs/celery.md` — background tasks, worker config
- `docs/testing.md` — test structure, fixtures, patterns, coverage
- `docs/migrations.md` — Alembic commands and rules
- `docs/observability.md` — Prometheus, Grafana, Loki, Tempo, alerts
- `docs/deployment.md` — Docker, volumes, SSH tunnels, env variables
- `docs/faq.md` — common questions and solutions
- `docs/runbooks.md` — alert runbooks (18 scenarios)

## Known Bugs

_None._
