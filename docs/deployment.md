# Docker и деплой

## Сервисы docker-compose

| Сервис | Порт (host:container) | Memory limit |
|--------|-----------------------|-------------|
| booking_back_service | 7777:8000 | 1GB |
| booking_celery_worker_service | - | 1GB |
| booking_celery_beat_service | - | 256MB |
| prometheus | 9090:9090 | 2GB |
| grafana | 3000:3000 | 512MB |
| loki | 3100:3100 | 512MB |
| tempo | 3200/4317/4318 | 512MB |
| promtail | 9080:9080 | 256MB |
| cadvisor | 8080:8080 | 512MB |
| node_exporter | 9100:9100 | 128MB |
| postgres_exporter | 9187:9187 | 128MB |
| redis_exporter | 9121:9121 | 64MB |
| celery_exporter | 9808:9808 | 128MB |
| blackbox_exporter | 9115:9115 | 64MB |

## Network

```bash
# Создать перед первым запуском
docker network create myNetwork
```

Все контейнеры — в `myNetwork` (external). Между собой обращаются по container_name.

## Volumes (persistent)

| Volume | Данные | Retention |
|--------|--------|-----------|
| prometheusdata | Метрики | 90 дней |
| grafanadata | Дашборды, плагины | - |
| lokidata | Логи | 7 дней |
| tempodata | Трейсы | 7 дней |
| imagesdata | Загруженные изображения | - |

## Деплой

```bash
# На сервере
git pull
docker compose build
docker compose up -d

# Перезапуск конкретного сервиса (без пересоздания зависимостей)
docker compose up -d --no-deps booking_back_service

# Сборка с версией
BUILD_VERSION=$(git rev-parse --short HEAD) docker compose build
```

## Особенности production (Linux)

- `extra_hosts: ["host.docker.internal:host-gateway"]` — обязательно для контейнеров, обращающихся к хосту
- Loki (`grafana/loki:latest` v3.x) — distroless, **нет** shell/wget/curl → healthcheck невозможен
- Grafana alerting file provisioning: `muteTimes:` и `policies:` **в разных файлах** (иначе ошибка валидации)
- Доступ к мониторингу — только через SSH tunnel, порты **не** открыты наружу

## SSH tunnel доступ

```bash
# Подключение с автоматическим проброском портов
ssh nas
# localhost:15432 → PostgreSQL
# localhost:16379 → Redis
# localhost:13000 → Grafana
```

---

## Переменные окружения

### Критичные (обязательные)

| Переменная | Описание |
|-----------|----------|
| `MODE` | `LOCAL` / `DEV` / `PROD` / `TEST` |
| `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASS`, `DB_NAME` | PostgreSQL |
| `REDIS_HOST`, `REDIS_PORT` | Redis |
| `JWT_SECRET_KEY` | Подпись токенов (менять на production!) |
| `JWT_ALGORITHM` | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Время жизни access token |
| `GF_ADMIN_PASSWORD` | Пароль Grafana admin |

### Опциональные

| Переменная | Default | Описание |
|-----------|---------|----------|
| `JWT_SECRET_KEY_PREVIOUS` | - | Предыдущий ключ (ротация без даунтайма) |
| `REFRESH_TOKEN_EXPIRE_DAYS` | 30 | Время жизни refresh token |
| `COOKIE_SECURE` | false | true для HTTPS |
| `AUTH_RATE_LIMIT` | 10/minute | Лимит на /register и /login |
| `LOG_LEVEL` | INFO | Уровень логирования |
| `LOG_JSON` | false | JSON формат логов |
| `METRICS_ENABLED` | true | Включить /metrics |
| `METRICS_TOKEN` | - | Bearer token для /metrics |
| `OTEL_ENABLED` | false | OpenTelemetry трейсинг |
| `OTEL_ENDPOINT` | http://tempo:4317 | OTLP gRPC endpoint |
| `OTEL_SAMPLE_RATE` | 1.0 | Процент трейсов (0.1 = 10%) |
| `SENTRY_DSN` | - | Sentry для error tracking |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD` | - | SMTP для email |
| `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` | - | Telegram алерты |
| `ALERT_EMAIL` | - | Email для critical алертов |
| `APP_VERSION` | dev | Версия в /health |
| `BUILD_VERSION` | dev | Docker build arg → APP_VERSION |

### Файлы

| Файл | Назначение |
|------|-----------|
| `.env` | Production/development переменные |
| `.env-test` | Тестовые переменные (`MODE=TEST`, отдельная БД) |
| `metrics_token` | Bearer token для Prometheus scraping |
