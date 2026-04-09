# Мониторинг и observability

## Стек

```
Приложение → Prometheus (метрики, 90 дней)
           → Loki (логи, 7 дней) ← Promtail (сбор из Docker)
           → Tempo (трейсы, 7 дней) ← OpenTelemetry
           → Grafana (дашборды + алерты → Telegram / Email)
```

## Exporters

| Exporter | Порт | Что собирает |
|----------|------|-------------|
| node_exporter | 9100 | CPU, RAM, диск, сеть хоста |
| postgres_exporter | 9187 | Connections, query duration, cache hit |
| redis_exporter | 9121 | Memory, ops/sec, evictions |
| celery_exporter | 9808 | Workers, queue length, task counts |
| cAdvisor | 8080 | CPU/memory/IO контейнеров |
| blackbox_exporter | 9115 | HTTP probes (health, hotels) |

## Бизнес-метрики (Prometheus)

| Метрика | Тип | Где инкрементируется |
|---------|-----|---------------------|
| `hotel_booking_bookings_created_total` | Counter | `POST /bookings` (успех) |
| `hotel_booking_bookings_cancelled_total` | Counter | `DELETE /bookings/{id}` |
| `hotel_booking_booking_failed_total` | Counter | `POST /bookings` (нет мест / номер не найден) |
| `hotel_booking_search_requests_total` | Counter | `GET /hotels` |

## Алерты (16 правил)

| Алерт | Severity | Порог |
|-------|----------|-------|
| High 5xx Rate | critical | >1% за 5m |
| SLO Fast Burn | critical | >5% за 5m |
| SLO Slow Burn | warning | >0.5% за 30m |
| Service Down | critical | absent(fastapi_requests_total) 5m |
| Service Health Degraded | critical | /health возвращает 503 |
| Endpoint Probe Failed | critical | blackbox probe failed 1m |
| Celery Worker Down | critical | absent(celery_worker_up) 2m |
| Celery Beat Down | critical | absent(container_memory) 2m |
| Celery Queue High | warning | queue > 50 tasks, 5m |
| Redis Down | critical | redis_up == 0, 1m |
| High Container Memory | warning | RSS > 500MB, 5m |
| High Container CPU | warning | >80%, 5m |
| High p99 Latency | warning | p99 > 500ms, 2m |
| Slow DB Query | warning | active TX > 30s |
| Disk Usage High | warning | >80% заполненность |
| DB Connections High | warning | >80% от max |
| Watchdog | - | Heartbeat (24h repeat) |

**Маршрутизация:** Critical → Telegram + Email, Warning → Telegram (подавляются ночью/выходные), Watchdog → отдельный канал (24h).

## Дашборд

`grafana/provisioning/dashboards/hotel-booking.json` — автоматически загружается через file provisioning. Панели:

- RPS, Error Rate, Latency percentiles (p50/p95/p99)
- SLO Status (Availability), Error Budget Remaining (30d)
- Container CPU/Memory (агрегация `sum by (name)` для multi-core)
- DB Connections, Max Active TX Duration
- Celery Workers, Queue Length, Active Tasks
- Log of All FastAPI App (Loki)
- Deploy annotations

## Логирование

Structured JSON logs (`src/logging_config.py`) с полями:
- `trace_id` — корреляция с трейсами (Tempo)
- `request_id` — X-Request-ID header
- `level` — INFO/WARNING/ERROR (Loki label для фильтрации)
