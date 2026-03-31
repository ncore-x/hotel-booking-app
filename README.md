# Hotel Booking API

REST API для поиска и бронирования отелей. FastAPI + PostgreSQL + Redis + Celery.

## Stack

- **Backend:** Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic
- **Database:** PostgreSQL (asyncpg), Redis (cache, rate limiting, Celery broker)
- **Tasks:** Celery (image resize, email notifications, DB backup)
- **Observability:** Prometheus, Grafana, Loki, Tempo (OpenTelemetry), Sentry
- **CI/CD:** GitLab CI, Docker

## Quick Start

```bash
# Prerequisites: Python 3.12+, PostgreSQL, Redis, uv

# Install dependencies
uv sync

# Copy and configure environment
cp .env.example .env
# Edit .env with your DB/Redis credentials and secrets

# Run migrations
uv run alembic upgrade head

# Start dev server
uv run uvicorn src.main:app --reload
```

API доступен на `http://localhost:8000/api/v1/`

## API

| Endpoint | Описание |
|----------|----------|
| `POST /api/v1/auth/register` | Регистрация |
| `POST /api/v1/auth/login` | Вход (устанавливает cookie) |
| `GET /api/v1/hotels` | Поиск отелей (фильтрация по датам) |
| `GET /api/v1/hotels/{id}/rooms` | Номера отеля |
| `POST /api/v1/bookings` | Бронирование |
| `GET /api/v1/bookings/me` | Мои бронирования |
| `GET /api/v1/health/live` | Health check |

Полная документация: `http://localhost:8000/docs` (Swagger) или `http://localhost:8000/redoc`

## Docker

```bash
# Development (full stack with monitoring)
docker compose up -d

# Production (app only, monitoring managed separately)
docker compose -f docker-compose-ci.yml up -d
```

## Tests

```bash
# Copy test env
cp .env.example .env-test
# Set MODE=TEST and AUTH_RATE_LIMIT=1000/minute in .env-test

# Run tests
uv run pytest tests/

# Lint & format
uv run ruff check src/ tests/
uv run ruff format src/ tests/
```

## Documentation

- [Developer Guide](docs/DEVELOPER_GUIDE.md) — архитектура, паттерны, API, деплой
- [Runbooks](docs/runbooks.md) — troubleshooting для каждого alert rule
- [.env.example](.env.example) — все переменные окружения с описанием

## Architecture

```
src/
├── api/          # FastAPI routers
├── services/     # Business logic
├── repositories/ # Database access (SQLAlchemy)
├── models/       # ORM models
├── schemas/      # Pydantic schemas
├── middleware/    # Prometheus, RequestID, JSON errors
├── tasks/        # Celery tasks
└── migrations/   # Alembic migrations
```

Request flow: `Router → Service → Repository → ORM`

## License

MIT
