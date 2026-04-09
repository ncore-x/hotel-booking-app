# Частые вопросы (FAQ)

## Как добавить новый endpoint?

1. Создай роутер в `src/api/` (или добавь в существующий)
2. Создай/обнови сервис в `src/services/`
3. Создай/обнови репозиторий в `src/repositories/` (если нужен новый запрос)
4. Добавь Pydantic схемы в `src/schemas/`
5. Добавь domain-исключение в `src/exceptions.py` + HTTP-исключение
6. Зарегистрируй роутер в `src/main.py`

## Как добавить новую модель?

1. Создай модель в `src/models/`
2. Добавь import в `src/models/__init__.py`
3. Создай миграцию: `uv run alembic revision --autogenerate -m "add_model_name"`
4. Примени: `uv run alembic upgrade head`
5. Создай репозиторий, маппер, схемы

## Как добавить Prometheus метрику?

1. Определи Counter/Gauge/Histogram в `src/middleware/prometheus.py`
2. Импортируй и инкрементируй в нужном месте (`src/api/*.py`)
3. Метрика автоматически появится на `/metrics`

## Почему на Grafana сервера "No data"?

- **SLO/Error Budget:** если нет 5xx-ответов, запрос возвращает пустую серию. Используй `or vector(0)` в числителе
- **Container метрики:** на multi-core сервере cAdvisor создаёт серию на каждый CPU core. Используй `sum(...) by (name)`
- **Prometheus только запустился:** метрикам нужно время для накопления (rate требует минимум 2 scrape)

## Почему контейнер перезапускается (Restarting)?

- `booking_back`: проверь `docker logs booking_back` — обычно `socket.gaierror` (DNS) или проблемы с БД
- `grafana`: проверь `docker logs grafana` — обычно ошибка в alerting provisioning файлах
- `loki`: если healthcheck unhealthy — это ложный отказ (distroless image, нет shell)

## Как подключиться к production БД?

```bash
ssh nas  # Автоматически пробрасывает порты
# DBeaver: localhost:15432, логин/пароль из .env
```

## Почему `docker restart` не помогает?

`docker restart` не перечитывает `docker-compose.yml`. Если менялись env vars, volumes или command — используй `docker compose up -d --no-deps <service>`.

## Как добавить алерт?

1. Добавь правило в `grafana/alerting/alert-rules.yaml`
2. Помни: `absent()` + `noDataState: Alerting` для "сервис не отвечает"; `noDataState: OK` для "метрика пропала потому что всё хорошо"
3. `docker compose up -d --no-deps grafana` для применения

## Как не потерять данные при обновлении?

Все данные в named volumes: `prometheusdata`, `grafanadata`, `lokidata`, `tempodata`, `imagesdata`. `docker compose down` **не** удаляет volumes. `docker compose down -v` — **удаляет** (не делай без необходимости).
