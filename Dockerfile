FROM python:3.12.11

RUN pip install uv

WORKDIR /app

COPY pyproject.toml ./

RUN uv sync

COPY . .

CMD [".venv/bin/python", "src/main.py"]
