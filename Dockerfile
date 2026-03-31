FROM python:3.12-slim

RUN pip install uv

RUN groupadd -r app && useradd -r -g app -d /app app

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

ARG BUILD_VERSION=dev
ENV APP_VERSION=${BUILD_VERSION}

COPY src/ src/
COPY tests/ tests/
COPY alembic.ini pytest.ini ./

RUN chown -R app:app /app
USER app

ENTRYPOINT ["sh", "-c", "\
  case \"$*\" in *pytest*|*ruff*) echo 'Skipping migrations';; *) \
  if [ -f alembic.ini ] && [ -d src/migrations ] && [ -n \"$DB_HOST\" ]; then \
  echo 'Applying migrations...' && uv run alembic upgrade head; \
  else echo 'Skipping migrations (no DB)'; fi;; esac && \
  exec \"$@\"", "--"]
CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
