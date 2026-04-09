# Миграции (Alembic)

## Основные команды

```bash
# Применить все миграции
uv run alembic upgrade head

# Создать миграцию (autogenerate)
uv run alembic revision --autogenerate -m "add_field_to_table"

# Пустая миграция (для ручных изменений)
uv run alembic revision -m "custom_change"

# Откатить на одну версию назад
uv run alembic downgrade -1

# Текущая версия
uv run alembic current

# История
uv run alembic history --verbose
```

## Правила

- Новые модели **обязательно** добавлять в `src/models/__init__.py` (для autogenerate)
- Файлы миграций — `src/migrations/versions/`
- Формат имён: `YYYY_MM_DD_HHMM-<revision>_<slug>.py`
- Все настройки — в `src/config.py` (`Settings`), **не** хардкодить в миграциях
