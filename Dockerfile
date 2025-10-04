FROM python:3.12.11

RUN pip install uv

WORKDIR /app

COPY pyproject.toml ./

RUN uv sync

# Копируем все файлы проекта
COPY . .

# Создаем entrypoint скрипт
RUN echo '#!/bin/sh\n\
set -e\n\
\n\
# Выполняем миграции если alembic настроен\n\
if [ -f "alembic.ini" ] && [ -d "migration" ]; then\n\
    echo "Applying database migrations..."\n\
    uv run alembic upgrade head\n\
else\n\
    echo "Alembic configuration not found, skipping migrations"\n\
    echo "Available directories:" && ls -la\n\
fi\n\
\n\
echo "Starting application..."\n\
exec "$@"\n\
' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
