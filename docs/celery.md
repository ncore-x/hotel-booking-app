# Celery задачи

## Конфигурация

**Broker:** Redis (`settings.REDIS_URL`)

| Задача | Расписание | Retries | Описание |
|--------|-----------|---------|----------|
| `resize_image` | По вызову | 3 (60s delay) | Создаёт версии 1000/500/200px |
| `send_checkin_email` | По вызову | 3 (60s delay) | Отправляет одно email уведомление |
| `booking_today_checkin` | 08:00 UTC daily | - | Ищет заезды сегодня, вызывает `send_checkin_email` |
| `backup_database` | 03:00 UTC daily | 2 (300s delay) | `pg_dump | gzip`, чистка старых |

## Worker параметры (production)

```bash
celery worker --concurrency=2 --max-tasks-per-child=50 --max-memory-per-child=400000
```

- `--concurrency=2` — 2 процесса (по умолчанию = кол-во CPU, что на 10-ядерном сервере = 10 x 400MB)
- `--max-tasks-per-child=50` — рециклирование после 50 задач
- `--max-memory-per-child=400000` — рециклирование при 400MB RSS

## Метрики (Prometheus)

Celery exporter (порт 9808) предоставляет:

| Метрика | Тип | Описание |
|---------|-----|----------|
| `celery_worker_up` | Gauge | 1 если воркер онлайн |
| `celery_queue_length` | Gauge | Глубина очереди по `queue_name` |
| `celery_task_runtime_sum` / `_count` | Counter | Суммарное и кол-во выполнений (без суффикса `_seconds`) |
| `celery_task_retried_total` | Counter | Кол-во повторных попыток |

Алерты на базе этих метрик: см. `hotel-booking-anomaly` группу в `grafana/alerting/alert-rules.yaml`.
