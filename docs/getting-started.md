# Быстрый старт

## Требования

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (package manager, **не** pip/poetry)
- PostgreSQL 15+
- Redis 7+

## Локальная разработка

```bash
# Установить зависимости
uv sync

# Скопировать и настроить env
cp .env.example .env
cp .env-test.example .env-test

# Применить миграции
uv run alembic upgrade head

# Запустить сервер
uv run uvicorn src.main:app --reload

# В отдельных терминалах (если нужны фоновые задачи):
uv run celery -A src.tasks.celery_app:celery_instance worker -l INFO
uv run celery -A src.tasks.celery_app:celery_instance beat -l INFO
```

## Проверка

```bash
# Lint + format
uv run ruff check src/ tests/
uv run ruff format src/ tests/

# Тесты
uv run pytest -v
```

API доступен на `http://localhost:8000/docs` (Swagger UI).
