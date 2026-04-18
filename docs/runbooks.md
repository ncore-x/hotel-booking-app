# Runbooks — Hotel Booking API

Дежурный справочник: что делать при срабатывании каждого alert rule.

**Стек мониторинга:** Prometheus → Grafana → Email
**Дашборд:** Grafana → FastAPI Observability
**Логи:** Grafana → Loki → фильтр `container_name=booking_back`
**Трейсы:** Grafana → Tempo

---

## Содержание

| Alert | Severity | Раздел |
|-------|----------|--------|
| [Service Down](#service-down) | critical | [↓](#service-down) |
| [Service Health Degraded](#service-health-degraded) | critical | [↓](#service-health-degraded) |
| [Endpoint Probe Failed](#endpoint-probe-failed) | critical | [↓](#endpoint-probe-failed) |
| [Hotels Probe Failed](#hotels-probe-failed) | critical | [↓](#hotels-probe-failed) |
| [SLO Fast Burn](#slo-fast-burn) | critical | [↓](#slo-fast-burn) |
| [SLO Slow Burn](#slo-slow-burn) | warning | [↓](#slo-slow-burn) |
| [High 5xx Rate](#high-5xx-rate) | critical | [↓](#high-5xx-rate) |
| [High p99 Latency](#high-p99-latency) | warning | [↓](#high-p99-latency) |
| [Redis Down](#redis-down) | critical | [↓](#redis-down) |
| [Celery Worker Down](#celery-worker-down) | critical | [↓](#celery-worker-down) |
| [Celery Beat Down](#celery-beat-down) | critical | [↓](#celery-beat-down) |
| [Celery Queue High](#celery-queue-high) | warning | [↓](#celery-queue-high) |
| [Slow DB Query](#slow-db-query) | warning | [↓](#slow-db-query) |
| [DB Connections High](#db-connections-high) | warning | [↓](#db-connections-high) |
| [High Container Memory](#high-container-memory) | warning | [↓](#high-container-memory) |
| [High Container CPU](#high-container-cpu) | warning | [↓](#high-container-cpu) |
| [Disk Usage High](#disk-usage-high) | warning | [↓](#disk-usage-high) |
| [Blackbox Exporter Down](#blackbox-exporter-down) | critical | [↓](#blackbox-exporter-down) |
| [Watchdog](#watchdog) | — | [↓](#watchdog) |

---

## Service Down

**Severity:** critical | **For:** 5m

**Что случилось:** Prometheus перестал получать метрики от `hotel_booking` — сервис не отвечает или упал.

**Что затронуто:** весь API недоступен — бронирования, поиск отелей, аутентификация.

### Диагностика

```bash
# Статус контейнера
docker ps -a | grep booking_back

# Последние логи
docker logs --tail=100 booking_back

# Проверить что порт поднят
curl -s http://localhost:7777/api/v1/health/live
```

Grafana: Loki → `{container_name="booking_back"} |= "ERROR"` за последние 10 минут.

### Исправление

1. **Контейнер упал** → `docker compose up -d booking_back_service`
2. **OOM killed** → проверить `docker inspect booking_back | grep OOMKilled`; если да — увеличить `memory limit` в `docker-compose.yml` или оптимизировать запросы
3. **Миграции зависли** → `docker logs booking_back` покажет alembic output; подключиться к БД и проверить `SELECT * FROM alembic_version`
4. **Порт занят** → `lsof -i :7777`; освободить порт или изменить маппинг

### Эскалация

Если сервис не поднимается за 10 минут — будить ответственного за инфра.

---

## Service Health Degraded

**Severity:** critical | **For:** 1m

**Что случилось:** `/api/v1/health` вернул 503 — БД или Redis недоступны, но сам процесс жив.

**Что затронуто:** зависит от компонента. Если упала БД — все операции с данными. Если Redis — auth (JWT blacklist), rate limiting, кэш.

### Диагностика

```bash
# Проверить состояние зависимостей
curl -s http://localhost:7777/api/v1/health | python3 -m json.tool

# PostgreSQL
docker ps | grep booking_db
docker logs --tail=50 booking_db

# Redis
docker ps | grep booking_cache
redis-cli -h localhost ping
```

### Исправление

**БД недоступна:**
1. `docker compose up -d booking_db` — поднять контейнер
2. Проверить дисковое место: `df -h` (PostgreSQL падает при 100% заполнении)
3. Проверить логи PostgreSQL: `docker logs booking_db --tail=50`

**Redis недоступен:**
1. `docker compose up -d booking_cache`
2. Приложение автоматически деградирует на InMemory-кэш — функциональность частично сохраняется
3. После восстановления Redis — перезапуск не нужен, reconnect происходит автоматически

### Эскалация

БД недоступна более 5 минут → проверить диск, RAM хоста, целостность data volume.

---

## Endpoint Probe Failed

**Severity:** critical | **For:** 1m

**Что случилось:** blackbox exporter не может достучаться до `/api/v1/health` — сервис недоступен извне (или внутри Docker-сети).

**Что затронуто:** внешняя доступность API — пользователи не могут подключиться.

### Диагностика

```bash
# Проверить что контейнер отвечает изнутри сети
docker exec blackbox_exporter wget -qO- http://booking_back_service:8000/api/v1/health

# Проверить DNS внутри Docker-сети
docker exec blackbox_exporter nslookup booking_back_service

# Проверить probe вручную
curl "http://localhost:9115/probe?target=http://booking_back_service:8000/api/v1/health&module=http_2xx_body&debug=true"
```

### Исправление

1. **Сервис упал** → см. [Service Down](#service-down)
2. **Сеть разорвана** → `docker network inspect myNetwork`; убедиться что `booking_back` и `blackbox_exporter` в одной сети
3. **Healthcheck вернул 503** → см. [Service Health Degraded](#service-health-degraded)
4. **Тело ответа не содержит `"status"`** → проверить формат ответа `/health` (module `http_2xx_body` проверяет body)

---

## Hotels Probe Failed

**Severity:** critical | **For:** 1m

**Что случилось:** blackbox probe на `/api/v1/hotels` упал — read path недоступен.

**Что затронуто:** пользователи не могут искать и просматривать отели.

### Диагностика

```bash
# Проверить endpoint вручную
curl -s "http://localhost:7777/api/v1/hotels" | head -c 200

# Проверить probe
curl "http://localhost:9115/probe?target=http://booking_back_service:8000/api/v1/hotels&module=http_2xx&debug=true"

# Логи ошибок hotels endpoint
docker logs --tail=100 booking_back | grep -E "hotels|500|ERROR"
```

### Исправление

1. **5xx на /hotels** → смотреть логи Loki: `{container_name="booking_back"} |= "hotels" |= "error"`
2. **БД недоступна** → см. [Service Health Degraded](#service-health-degraded)
3. **Таймаут** → проверить медленные запросы в Grafana (DB Max Active Transaction Duration)

---

## SLO Fast Burn

**Severity:** critical | **For:** 1m

**Что случилось:** более 5% запросов отдают 5xx в течение последних 5 минут — бюджет ошибок сгорит за несколько часов.

**Что затронуто:** значительная часть пользователей получает ошибки.

### Диагностика

```bash
# Какие именно endpoints ломаются
# Grafana → Loki: {container_name="booking_back"} |= "500"

# Топ ошибок за последние 10 минут
docker logs --tail=500 booking_back 2>&1 | grep -E "ERROR|500" | sort | uniq -c | sort -rn | head -20
```

Grafana: панель **Percent of 5xx** → смотреть на какие пути приходятся ошибки.

### Исправление

1. **Недавний деплой** → `git log --oneline -5`; если причина в нём — откатить: `docker compose up -d` с предыдущим образом
2. **БД перегружена** → см. [Slow DB Query](#slow-db-query), [DB Connections High](#db-connections-high)
3. **OOM/краш воркера** → проверить [High Container Memory](#high-container-memory)
4. **Внешняя зависимость** → проверить SMTP, S3 если используются

### Эскалация

Если ошибки не прекращаются за 15 минут — переводить на режим обслуживания.

---

## SLO Slow Burn

**Severity:** warning | **For:** 5m

**Что случилось:** более 0.5% запросов отдают 5xx за последние 30 минут — при таком темпе месячный бюджет ошибок исчерпается за ~3 дня.

### Диагностика

Аналогично [SLO Fast Burn](#slo-fast-burn), но с окном 30m в запросах.

```bash
# Ищем редкие, но стабильные ошибки
docker logs --tail=1000 booking_back 2>&1 | grep "ERROR" | grep -oP '"\w+": "\w+"' | sort | uniq -c
```

### Исправление

1. Найти паттерн ошибок — конкретный endpoint, конкретный тип исключения
2. Проверить нет ли race condition или деградирующего внешнего сервиса
3. Если ошибки нарастают — готовиться к деплою фикса до срабатывания Fast Burn

---

## High 5xx Rate

**Severity:** critical | **For:** 2m

**Что случилось:** более 1% запросов отдают 5xx на протяжении 2 минут.

Более ранний сигнал, чем SLO Fast Burn (5%).

### Диагностика и исправление

→ Действия идентичны [SLO Fast Burn](#slo-fast-burn): смотри секцию Диагностика и Исправление там.

---

## High p99 Latency

**Severity:** warning | **For:** 2m

**Что случилось:** 99-й перцентиль времени ответа превысил 500ms.

**Что затронуто:** медленные ответы для части пользователей; бронирование и поиск тормозят.

### Диагностика

Grafana:
- Панель **P99 Duration** — динамика latency
- Панель **Latency Percentiles** — сравнение p50/p95/p99
- Панель **DB Max Active Transaction Duration** — не завис ли долгий запрос

```bash
# Активные запросы к БД прямо сейчас
docker exec booking_db psql -U ${DB_USER} -d ${DB_NAME} \
  -c "SELECT pid, now() - query_start AS duration, state, query FROM pg_stat_activity WHERE state='active' ORDER BY duration DESC LIMIT 10;"
```

Grafana → Tempo: найти трейсы с latency > 500ms, посмотреть где именно тратится время.

### Исправление

1. **Медленный SQL** → `EXPLAIN ANALYZE` подозрительного запроса; добавить индекс или оптимизировать
2. **Lock contention** → проверить `pg_locks` + `pg_stat_activity`; найти блокирующую транзакцию и завершить: `SELECT pg_terminate_backend(pid)`
3. **Redis медленный** → проверить `redis-cli latency latest`
4. **Высокая нагрузка** → посмотреть [High Container CPU](#high-container-cpu)

---

## Redis Down

**Severity:** critical | **For:** 1m

**Что случилось:** `redis_up == 0` или redis_exporter не получает метрики — Redis недоступен.

**Что затронуто:**
- **Auth** — JWT blacklist не работает (выход из системы не блокирует токены)
- **Rate limiting** — лимиты не применяются (риск брутфорса)
- **Кэш** — приложение переходит на InMemory; производительность деградирует
- **Celery** — новые задачи не ставятся в очередь

### Диагностика

```bash
docker ps | grep booking_cache
docker logs --tail=50 booking_cache
redis-cli -h localhost -p 6379 ping
```

### Исправление

1. `docker compose up -d booking_cache`
2. Дождаться ping → приложение переподключится автоматически
3. Проверить диск: Redis падает при нехватке места для AOF/RDB-снапшота

### Эскалация

Redis недоступен > 5 минут → повышенный риск security (rate limiting выключен). Рассмотреть временную блокировку эндпоинтов регистрации/логина.

---

## Celery Worker Down

**Severity:** critical | **For:** 2m

**Что случилось:** `celery_worker_up == 0` или метрики отсутствуют — воркеры не обрабатывают задачи.

**Что затронуто:** фоновые задачи не выполняются — ресайз изображений, отправка писем.

### Диагностика

```bash
docker ps | grep booking_celery_worker
docker logs --tail=100 booking_celery_worker

# Очередь задач в Redis
redis-cli -h localhost llen celery
```

### Исправление

1. `docker compose up -d booking_celery_worker_service`
2. **OOM kill** → проверить `docker inspect booking_celery_worker | grep OOMKilled`; если да — снизить `--concurrency` или увеличить лимит памяти
3. **Unhandled exception** → логи покажут traceback; исправить задачу и задеплоить
4. **Redis недоступен** → воркер не может подключиться к broker; сначала поднять Redis

---

## Celery Beat Down

**Severity:** critical | **For:** 2m

**Что случилось:** cAdvisor не видит контейнер `booking_celery_beat` — планировщик остановлен.

**Что затронуто:** не запускаются scheduled tasks — ежедневные email о заезде (8:00 UTC) и бэкапы БД (03:00 UTC).

### Диагностика

```bash
docker ps | grep booking_celery_beat
docker logs --tail=50 booking_celery_beat
```

### Исправление

1. `docker compose up -d booking_celery_beat_service`
2. Если упал в нерабочее время — beat не догоняет пропущенные задачи. Запустить вручную:

   ```bash
   docker exec booking_celery_worker uv run celery --app=src.tasks.celery_app:celery_instance call src.tasks.email_tasks.send_emails_to_users_with_today_checkin
   ```

### Эскалация

Beat не поднимается за 10 минут → проверить нет ли ошибок в конфиге задач (`celeryconfig`); если ближайшая задача по расписанию критична (рассылка, бэкап) — запустить вручную.

---

## Celery Queue High

**Severity:** warning | **For:** 5m

**Что случилось:** в очереди Celery более 50 задач — воркеры не справляются.

**Что затронуто:** ресайз изображений и отправка email работают с задержкой.

### Диагностика

```bash
# Размер очереди
redis-cli -h localhost llen celery

# Активные воркеры и их статус
docker exec booking_celery_worker uv run celery --app=src.tasks.celery_app:celery_instance inspect active

# Что тормозит
docker logs --tail=200 booking_celery_worker | grep -E "Task|ERROR|retry"
```

### Исправление

1. **Временный всплеск** — подождать 10 минут, очередь разберётся сама
2. **Воркеры зависли** → `docker restart booking_celery_worker`
3. **Задача в бесконечном retry** → найти в логах; при необходимости сбросить очередь: `redis-cli del celery` (⚠️ все задачи потеряются)
4. **Недостаточно воркеров** → увеличить `--concurrency` в docker-compose (с учётом лимита памяти)

---

## Slow DB Query

**Severity:** warning | **For:** 1m

**Что случилось:** активная транзакция PostgreSQL выполняется более 30 секунд — lock contention или медленный запрос без индекса.

**Что затронуто:** запросы, ожидающие заблокированную таблицу, встают в очередь → рост latency → возможный каскад 5xx.

### Диагностика

```bash
# Долгие активные транзакции
docker exec booking_db psql -U ${DB_USER} -d ${DB_NAME} -c "
SELECT pid, now() - query_start AS duration, state, wait_event_type, wait_event, left(query, 100)
FROM pg_stat_activity
WHERE state = 'active' AND now() - query_start > interval '10s'
ORDER BY duration DESC;"

# Блокировки
docker exec booking_db psql -U ${DB_USER} -d ${DB_NAME} -c "
SELECT blocked.pid, blocked.query, blocking.pid AS blocking_pid, blocking.query AS blocking_query
FROM pg_stat_activity blocked
JOIN pg_stat_activity blocking ON blocking.pid = ANY(pg_blocking_pids(blocked.pid));"
```

### Исправление

1. **Заблокированная транзакция** → найти blocking_pid и завершить: `SELECT pg_terminate_backend(<blocking_pid>);`
2. **Медленный SELECT** → `EXPLAIN ANALYZE <query>`; добавить индекс или переписать запрос
3. **SELECT FOR UPDATE завис** → проверить нет ли deadlock в логах; перезапустить зависший запрос

---

## DB Connections High

**Severity:** warning | **For:** 3m

**Что случилось:** используется более 80% от `max_connections` PostgreSQL — риск `connection refused` при пике.

**Что затронуто:** новые запросы могут получить ошибку подключения к БД.

### Диагностика

```bash
# Текущее использование соединений
docker exec booking_db psql -U ${DB_USER} -d ${DB_NAME} -c "
SELECT count(*), state FROM pg_stat_activity GROUP BY state;"

# Максимум соединений
docker exec booking_db psql -U ${DB_USER} -d ${DB_NAME} -c "SHOW max_connections;"
```

### Исправление

1. **Утечка соединений** → найти соединения в состоянии `idle` более часа; перезапустить их источник
2. **Пул исчерпан** → уменьшить `DB_POOL_SIZE` в `.env` или добавить PgBouncer
3. **Временный пик** → подождать; соединения закроются после завершения запросов
4. **Долгие транзакции удерживают соединения** → см. [Slow DB Query](#slow-db-query)

---

## High Container Memory

**Severity:** warning | **For:** 5m

**Что случилось:** контейнер `booking_back`, `booking_celery_worker` или `booking_celery_beat` потребляет более 500MB RSS.

### Диагностика

```bash
# Текущее потребление памяти всех контейнеров
docker stats --no-stream --format "table {{.Name}}\t{{.MemUsage}}\t{{.MemPerc}}"

# Детали по конкретному контейнеру (из алерта: $labels.name)
docker stats --no-stream <container_name>
```

Grafana: панель **Container Memory RSS** — посмотреть динамику роста.

### Исправление

**`booking_back` (API):**
- Утечка памяти → Grafana → Tempo, отсортировать по duration, найти запросы >2s; перезапустить контейнер если RSS продолжает расти: `docker restart booking_back`
- Высокий трафик → ничего делать не нужно; при OOM контейнер перезапустится сам (`restart: unless-stopped`)

**`booking_celery_worker`:**
- `--max-memory-per-child=400000` должен рециклировать воркер-процесс после 400MB
- Если RSS растёт выше лимита — снизить `--max-memory-per-child` или `--concurrency`

1. Краткосрочно: `docker restart <container_name>`
2. Долгосрочно: найти источник утечки через профилировщик памяти

---

## High Container CPU

**Severity:** warning | **For:** 5m

**Что случилось:** контейнер использует более 80% CPU на протяжении 5 минут.

### Диагностика

```bash
docker stats --no-stream <container_name>

# Топ процессов внутри контейнера
docker exec <container_name> top -bn1 | head -20
```

Grafana → Tempo: найти долгие CPU-bound трейсы (сортировка по duration).

### Исправление

1. **Временный пик** (деплой, прогрев кэша) → подождать 2-3 минуты
2. **CPU-bound задача** → найти через профилировщик; оптимизировать алгоритм или вынести в Celery
3. **Celery воркер занят тяжёлыми задачами** → снизить `--concurrency` или разделить на отдельные очереди
4. **Бесконечный цикл** → перезапустить контейнер; найти и исправить баг

---

## Disk Usage High

**Severity:** warning | **For:** 5m

**Что случилось:** файловая система заполнена более чем на 80%.

**Что затронуто:** зависит от partition:
- `/` или `/var` → Docker не сможет создавать новые слои/тома; PostgreSQL упадёт при 100%
- Partition с `imagesdata` → загрузка новых изображений упадёт с ошибкой

### Диагностика

```bash
# Что занимает место
df -h
du -sh /var/lib/docker/* 2>/dev/null | sort -rh | head -10

# Docker-специфично: dangling images и volumes
docker system df
```

### Исправление

1. **Docker мусор** → `docker system prune -f` (удалит остановленные контейнеры, dangling images, неиспользуемые сети)
2. **Старые образы** → `docker image prune -a --filter "until=168h"` (образы старше 7 дней)
3. **Логи контейнеров** → ротация уже настроена (max-size/max-file), но если логи старые: `find /var/lib/docker/containers -name "*.log" -size +100M`
4. **Бэкапы БД** → `ls -lh backups/`; старые удаляются автоматически через `BACKUP_RETAIN_DAYS=7`, но можно очистить вручную
5. **Изображения отелей** → `du -sh src/static/images/`; удалить неиспользуемые через API или вручную

### Эскалация

Диск > 90% → немедленные действия, PostgreSQL упадёт при 100%.

---

## Blackbox Exporter Down

**Severity:** critical | **For:** 1m

**Что случилось:** Prometheus не получает метрики от blackbox_exporter — HTTP-пробы не выполняются, внешняя доступность не проверяется.

**Что затронуто:** мониторинг внешней доступности слеп — [Endpoint Probe Failed](#endpoint-probe-failed) и [Hotels Probe Failed](#hotels-probe-failed) не сработают.

### Диагностика

```bash
docker ps | grep blackbox_exporter
docker logs --tail=50 blackbox_exporter
curl -s http://localhost:9115 | head -5
```

### Исправление

1. `docker compose up -d blackbox_exporter`
2. Проверить что `blackbox.yml` не повреждён: `docker exec blackbox_exporter cat /etc/blackbox_exporter/config.yml`

### Эскалация

Blackbox не поднимается → алерты [Endpoint Probe Failed](#endpoint-probe-failed) и [Hotels Probe Failed](#hotels-probe-failed) слепые. Временно усилить мониторинг логов: `docker logs -f booking_back | grep -E "ERROR|500"`.

---

## Watchdog

**Severity:** watchdog (информационный)

**Что случилось:** Watchdog **перестал** приходить — это значит alerting pipeline сломан.

Watchdog приходит каждые 24 часа и сигнализирует что alerting pipeline работает. Если он не пришёл — проблема в самом мониторинге.

### Диагностика

```bash
# Grafana работает?
curl -s http://localhost:3000/api/health

# Prometheus работает?
curl -s http://localhost:9090/-/healthy

```

### Исправление

1. **Grafana упала** → `docker compose up -d grafana`
2. **Prometheus упал** → `docker compose up -d prometheus`
3. **Alert rules не загрузились** → Grafana UI → Alerting → Alert rules; проверить нет ли ошибок провижининга

---

## Общие команды

```bash
# Статус всех сервисов
docker compose ps

# Перезапустить конкретный сервис
docker compose up -d --no-deps <service_name>

# Посмотреть логи с фильтром
docker logs --tail=200 --follow booking_back 2>&1 | grep ERROR

# Войти в контейнер
docker exec -it booking_back sh

# Метрики Prometheus прямо сейчас
curl -H "Authorization: Bearer $(cat metrics_token)" http://localhost:7777/metrics | grep fastapi_requests

# Статус Prometheus targets
curl -s http://localhost:9090/api/v1/targets | python3 -m json.tool | grep -E "health|job"
```
