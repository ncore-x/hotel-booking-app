FROM python:3.12.11

RUN pip install uv

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen

# Версия сборки — передаётся через --build-arg BUILD_VERSION=$(git rev-parse --short HEAD)
# Читается приложением через settings.APP_VERSION (env var APP_VERSION)
ARG BUILD_VERSION=dev
ENV APP_VERSION=${BUILD_VERSION}

# Копируем все файлы проекта
COPY . .

# Создаем entrypoint скрипт
RUN echo '#!/bin/sh\n\
set -e\n\
\n\
# Выполняем миграции только для сервера — не для pytest/ruff\n\
case "$*" in\n\
    *pytest*|*ruff*)\n\
        echo "Skipping migrations for lint/test command"\n\
        ;;\n\
    *)\n\
        if [ -f "alembic.ini" ] && [ -d "src/migrations" ] && [ -n "$DB_HOST" ]; then\n\
            echo "Applying database migrations..."\n\
            uv run alembic upgrade head\n\
        else\n\
            echo "Skipping migrations (no DB_HOST or alembic config not found)"\n\
        fi\n\
        ;;\n\
esac\n\
\n\
echo "Starting application..."\n\
exec "$@"\n\
' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
