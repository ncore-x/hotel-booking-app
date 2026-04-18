# Мониторинг и observability

## Стек

```
Приложение → Prometheus (метрики, 90 дней)
           → Loki (логи, 7 дней) ← Promtail (сбор из Docker)
           → Tempo (трейсы, 7 дней) ← OpenTelemetry
           → Grafana (дашборды + алерты → Email)
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

## Алерты

Два группы правил в `grafana/alerting/alert-rules.yaml`:

### Группа `hotel-booking` — базовые пороговые алерты (17 правил)

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

### Группа `hotel-booking-anomaly` — алерты отклонения от базовой линии (22 правила)

Каждое правило сравнивает текущее значение с baseline через `offset` и паттерн `/ (metric offset Xm > guard)` для защиты от деления на ноль.

| Алерт | Severity | Метрика / Условие |
|-------|----------|-------------------|
| CPU Spike vs Baseline | warning | CPU в 1.5× выше чем 5m назад |
| p95 Latency Spike vs Baseline | warning | p95 в 2× выше чем 10m назад |
| DB Connections Spike vs Baseline | warning | соединения в 1.8× выше чем 15m назад |
| Celery Queue Depth Spike | warning | queue > 100 задач |
| RPS Drop vs Baseline | warning | RPS < 50% от значения 10m назад |
| 5xx Error Rate Spike vs Baseline | critical | доля 5xx в 3× выше чем 10m назад |
| 4xx Error Rate Spike vs Baseline | warning | 4xx в 5× выше чем 10m назад |
| Slow DB Queries Spike vs Baseline | warning | время запросов в 3× выше чем 10m назад |
| DB Locks Spike | warning | блокировки в 3× выше чем 10m назад |
| Redis Cache Hit Ratio Drop | warning | hit ratio < 80% |
| Container Memory Spike vs Baseline | warning | память в 1.5× выше чем 30m назад |
| OOM Kill Detected | critical | increase(container_oom_events_total[5m]) > 0 |
| Disk Full Prediction < 24h | warning | predict_linear диск заполнится за 24h |
| File Descriptors > 80% Limit | warning | process_open_fds / process_max_fds > 0.8 |
| Probe Duration Spike vs Baseline | warning | probe latency в 3× выше чем 10m назад |
| Redis Evictions Spike | warning | evictions > 10/min |
| Redis Memory > 80% of Limit | warning | used / max_bytes > 0.8 |
| Celery Task Runtime Spike vs Baseline | warning | avg runtime в 2× выше чем 15m назад |
| Celery Task Retries Spike | warning | retries в 5× выше чем 10m назад |
| Container Restart Rate Spike | critical | >3 рестарта за 15m |
| TCP Retransmissions Spike vs Baseline | warning | retransmits в 5× выше чем 10m назад |
| 401 Unauthorized Spike vs Baseline | warning | 401 в 10× выше чем 10m назад (brute-force) |

**Маршрутизация:** Critical → Email, Warning → Email (подавляются ночью/выходные), Watchdog → отдельный канал (24h).

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
