# Developer Guide — Hotel Booking API

Документация для разработчиков. Обновляется по мере развития проекта.

---

## Содержание

1. [Быстрый старт](#1-быстрый-старт)
2. [Архитектура](#2-архитектура)
3. [Структура проекта](#3-структура-проекта)
4. [API Endpoints](#4-api-endpoints)
5. [Модели и схемы](#5-модели-и-схемы)
6. [Паттерны кода](#6-паттерны-кода)
7. [Celery задачи](#7-celery-задачи)
8. [Тестирование](#8-тестирование)
9. [Миграции](#9-миграции-alembic)
10. [Мониторинг и observability](#10-мониторинг-и-observability)
11. [Docker и деплой](#11-docker-и-деплой)
12. [Переменные окружения](#12-переменные-окружения)
13. [Частые вопросы (FAQ)](#13-частые-вопросы-faq)

---

## 1. Быстрый старт

### Требования

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (package manager, **не** pip/poetry)
- PostgreSQL 15+
- Redis 7+

### Локальная разработка

```bash
# Установить зависимости
uv sync

# Скопировать и настроить env
cp .env.example .env
cp .env-test.example .env-test

# Применить миграции
uv run alembic upgrade head

# Запустить сервер
uv run uvicorn src.main:app --reload

# В отдельных терминалах (если нужны фоновые задачи):
uv run celery -A src.tasks.celery_app:celery_instance worker -l INFO
uv run celery -A src.tasks.celery_app:celery_instance beat -l INFO
```

### Проверка

```bash
# Lint + format
uv run ruff check src/ tests/
uv run ruff format src/ tests/

# Тесты
uv run pytest -v
```

API доступен на `http://localhost:8000/docs` (Swagger UI).

---

## 2. Архитектура

### Слои (сверху вниз)

```
HTTP Request
    │
    ▼
┌──────────────────────────────────────┐
│  Middleware (CORS, GZip, Prometheus,  │
│  RequestID, JSONErrorHandler)         │
└──────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────┐
│  API Layer (src/api/)                │
│  Роутеры, валидация, маппинг ошибок │
└──────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────┐
│  Service Layer (src/services/)       │
│  Бизнес-логика, оркестрация          │
└──────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────┐
│  Repository Layer (src/repositories/)│
│  SQL-запросы, маппинг ORM → Pydantic │
└──────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────┐
│  Database (PostgreSQL + Redis)       │
└──────────────────────────────────────┘
```

### Ключевые принципы

- **Service никогда не бросает HTTPException** — только domain-исключения из `src/exceptions.py`
- **API-слой ловит domain-исключения и переводит в HTTP** — `except HotelNotFoundException: raise HotelNotFoundHTTPException()`
- **Один DBManager на запрос** — все репозитории делят одну сессию (Unit of Work)
- **Commit явный** — `await db.commit()` вызывается в сервисе, rollback автоматический

---

## 3. Структура проекта

```
src/
├── api/                        # Роутеры (HTTP → Service)
│   ├── dependencies.py         # DI: DBDep, UserIdDep, AdminDep, PaginationDep
│   ├── auth.py                 # /auth/*
│   ├── hotels.py               # /hotels/*
│   ├── rooms.py                # /hotels/{id}/rooms/*
│   ├── bookings.py             # /bookings/*
│   ├── facilities.py           # /facilities/*
│   ├── images.py               # /hotels/{id}/images/*
│   └── health.py               # /health, /health/live
│
├── services/                   # Бизнес-логика
│   ├── base.py                 # BaseService(db: DBManager)
│   ├── auth.py                 # JWT, хеширование, логин/регистрация
│   ├── hotels.py               # CRUD отелей + фильтрация по датам
│   ├── rooms.py                # CRUD номеров + availability
│   ├── bookings.py             # Бронирования (SELECT FOR UPDATE)
│   ├── facilities.py           # Справочник удобств
│   ├── images.py               # Загрузка изображений + PIL валидация
│   └── token_blacklist.py      # JWT blacklist через Redis
│
├── repositories/               # Доступ к данным
│   ├── base.py                 # BaseRepository (CRUD generics)
│   ├── utils.py                # rooms_ids_for_booking() — CTE запрос доступности
│   ├── hotels.py               # Фильтрация с учётом свободных номеров
│   ├── rooms.py                # selectinload(facilities), count queries
│   ├── bookings.py             # add_booking с row lock, today checkins
│   ├── users.py                # Password/email update
│   ├── facilities.py           # M2M rooms↔facilities
│   ├── hotel_images.py         # Image records
│   └── mappers/mappers.py      # ORM → Pydantic через model_validate
│
├── models/                     # SQLAlchemy ORM
│   ├── users.py                # users (email, hashed_password, is_admin)
│   ├── hotels.py               # hotels (title, location) + UNIQUE constraint
│   ├── rooms.py                # rooms (hotel_id FK, price, quantity)
│   ├── bookings.py             # bookings (user_id, room_id, date_from, date_to)
│   ├── facilities.py           # facilities + rooms_facilities (M2M)
│   └── hotel_images.py         # hotel_images (hotel_id FK, filename)
│
├── schemas/                    # Pydantic (валидация + сериализация)
│   ├── common.py               # PaginatedResponse[T]
│   ├── users.py                # UserRequestAdd, User, LoginResponse
│   ├── hotels.py               # HotelAdd, HotelPatch, Hotel
│   ├── rooms.py                # RoomAddRequest, RoomPatchRequest, Room, RoomWithRels
│   ├── bookings.py             # BookingAddRequest, BookingPatchRequest, Booking
│   ├── facilities.py           # FacilityAdd, Facility
│   └── images.py               # HotelImageAdd, HotelImage, ImageUploadResponse
│
├── middleware/                 # HTTP middleware
│   ├── prometheus.py           # Метрики + бизнес-счётчики
│   ├── request_id.py           # X-Request-ID
│   └── json_error_handler.py   # Человекочитаемые ошибки JSON парсинга
│
├── tasks/                      # Celery
│   ├── celery_app.py           # Celery instance + beat schedule
│   ├── tasks.py                # resize_image, send_checkin_email
│   └── backup.py               # backup_database (pg_dump + gzip)
│
├── migrations/                 # Alembic
│   ├── env.py
│   └── versions/               # Файлы миграций
│
├── config.py                   # Settings (все env-переменные)
├── database.py                 # Engine, session factory, Base
├── exceptions.py               # Domain + HTTP исключения
├── main.py                     # FastAPI app, middleware, роутеры
├── logging_config.py           # JSON/text логирование
├── tracing.py                  # OpenTelemetry → Tempo
├── limiter.py                  # Rate limiter (slowapi)
└── init.py                     # Redis manager
```

---

## 4. API Endpoints

### Auth (`/auth`)

| Метод | Endpoint | Описание | Auth | Rate limit |
|-------|----------|----------|------|------------|
| POST | `/auth/register` | Регистрация | - | AUTH_RATE_LIMIT |
| POST | `/auth/login` | Вход (устанавливает cookies) | - | AUTH_RATE_LIMIT |
| GET | `/auth/me` | Профиль текущего пользователя | JWT | - |
| PATCH | `/auth/me` | Сменить пароль | JWT | - |
| PATCH | `/auth/me/email` | Сменить email | JWT | - |
| POST | `/auth/refresh` | Обновить access token | refresh cookie | - |
| POST | `/auth/logout` | Blacklist токенов, очистка cookies | JWT | - |

**JWT:** Access token (короткоживущий) + Refresh token (30 дней). Оба в httponly cookies.
**Key rotation:** Если установлен `JWT_SECRET_KEY_PREVIOUS`, старые токены валидны.

### Hotels (`/hotels`)

| Метод | Endpoint | Описание | Auth | Пагинация |
|-------|----------|----------|------|-----------|
| GET | `/hotels` | Список отелей (с фильтром по датам) | - | да |
| GET | `/hotels/{id}` | Один отель | - | - |
| POST | `/hotels` | Создать отель | Admin | - |
| PUT | `/hotels/{id}` | Полное обновление | Admin | - |
| PATCH | `/hotels/{id}` | Частичное обновление | Admin | - |
| DELETE | `/hotels/{id}` | Удалить (если нет номеров) | Admin | - |

**GET /hotels query params:** `date_from`, `date_to` (required), `location`, `title`, `sort_by`, `order`, `page`, `per_page`

### Rooms (`/hotels/{hotel_id}/rooms`)

| Метод | Endpoint | Описание | Auth |
|-------|----------|----------|------|
| GET | `/hotels/{id}/rooms` | Свободные номера в диапазоне дат | - |
| GET | `/hotels/{id}/rooms/{room_id}` | Один номер с удобствами | - |
| POST | `/hotels/{id}/rooms` | Создать номер | Admin |
| PUT | `/hotels/{id}/rooms/{room_id}` | Полное обновление | Admin |
| PATCH | `/hotels/{id}/rooms/{room_id}` | Частичное обновление | Admin |
| DELETE | `/hotels/{id}/rooms/{room_id}` | Удалить (если нет бронирований) | Admin |

### Bookings (`/bookings`)

| Метод | Endpoint | Описание | Auth |
|-------|----------|----------|------|
| GET | `/bookings/me` | Мои бронирования | JWT |
| GET | `/bookings/{id}` | Одно бронирование (проверка владельца) | JWT |
| POST | `/bookings` | Забронировать (с row lock) | JWT |
| PATCH | `/bookings/{id}` | Изменить даты (атомарно) | JWT |
| DELETE | `/bookings/{id}` | Отменить | JWT |

### Facilities (`/facilities`)

| Метод | Endpoint | Описание | Auth | Кэш |
|-------|----------|----------|------|-----|
| GET | `/facilities` | Список удобств | - | 300s |
| POST | `/facilities` | Создать удобство | Admin | clears cache |

### Images (`/hotels/{hotel_id}/images`)

| Метод | Endpoint | Описание | Auth |
|-------|----------|----------|------|
| POST | `/hotels/{id}/images` | Загрузить изображение (JPEG/PNG/WebP, max 5MB) | Admin |
| GET | `/hotels/{id}/images` | Список изображений отеля | - |

### Health (`/health`)

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/api/v1/health` | Полная проверка (DB + Redis) + version |
| GET | `/api/v1/health/live` | Liveness probe (200 OK) |

### Metrics

| Метод | Endpoint | Описание | Auth |
|-------|----------|----------|------|
| GET | `/metrics` | Prometheus метрики | Bearer (METRICS_TOKEN) |

---

## 5. Модели и схемы

### Соглашения по именованию схем

| Суффикс | Назначение | Пример |
|---------|------------|--------|
| `*AddRequest` | Входные данные от клиента (с валидацией) | `BookingAddRequest` |
| `*PatchRequest` | Частичное обновление от клиента | `RoomPatchRequest` |
| `*Add` | Данные для записи в БД (+ computed fields) | `BookingAdd` (включает `price`, `user_id`) |
| `*Patch` | Данные для частичного обновления в БД | `HotelPatch` |
| Без суффикса | Ответ клиенту (включает `id`) | `Hotel`, `Room`, `Booking` |
| `*WithRels` | Ответ с вложенными связями | `RoomWithRels` (включает `facilities`) |

### Таблицы БД

```
users
  ├── id (PK), email (UNIQUE), hashed_password, is_admin
  └── created_at, updated_at

hotels
  ├── id (PK), title, location
  ├── UNIQUE(title, location) — uq_hotels_title_location
  ├── GIN INDEX(title, location) — pg_trgm для поиска
  └── created_at, updated_at

rooms
  ├── id (PK), hotel_id (FK → hotels), title, description, price, quantity
  ├── INDEX(hotel_id)
  └── created_at, updated_at

bookings
  ├── id (PK), user_id (FK → users), room_id (FK → rooms)
  ├── date_from, date_to, price
  ├── INDEX(user_id), INDEX(room_id), INDEX(date_from)
  └── created_at, updated_at

facilities
  ├── id (PK), title (UNIQUE — uq_facilities_title)

rooms_facilities (M2M)
  ├── room_id (FK → rooms, CASCADE), facility_id (FK → facilities)
  └── PK(room_id, facility_id)

hotel_images
  ├── id (PK), hotel_id (FK → hotels, CASCADE), filename, content_type
  ├── INDEX(hotel_id)
  └── created_at
```

### Пагинация

Все list-эндпоинты возвращают `PaginatedResponse[T]`:

```json
{
  "items": [...],
  "total": 42,
  "page": 1,
  "per_page": 10,
  "pages": 5,
  "has_next": true,
  "has_prev": false
}
```

---

## 6. Паттерны кода

### Dependency Injection

```python
# src/api/dependencies.py

DBDep       = Annotated[DBManager, Depends(get_db)]        # Сессия БД
UserIdDep   = Annotated[int, Depends(get_current_user_id)]  # Авторизованный юзер
AdminDep    = Annotated[int, Depends(get_current_admin)]    # Администратор
PaginationDep = Annotated[PaginationParams, Depends()]      # page + per_page
```

**DBManager** — Unit of Work. Предоставляет все репозитории через одну сессию:

```python
async with DBManager(session_factory=async_session_maker) as db:
    db.hotels      # HotelsRepository
    db.rooms       # RoomsRepository
    db.bookings    # BookingsRepository
    db.users       # UsersRepository
    db.facilities  # FacilitiesRepository
    db.hotel_images # HotelImagesRepository
    await db.commit()  # Явный commit
    # Rollback автоматический при исключении
```

### Исключения — два параллельных дерева

```python
# Domain (services/repositories бросают):
class HotelNotFoundException(NabronirovalException):
    detail = "Отель не найден"

# HTTP (API-слой ловит и пробрасывает):
class HotelNotFoundHTTPException(NabronirovalHTTPException):
    status_code = 404
    detail = "Отель не найден"

# Паттерн использования в роутере:
try:
    hotel = await HotelService(db).get_hotel(hotel_id)
except HotelNotFoundException:
    raise HotelNotFoundHTTPException()
```

### Уникальные ограничения

Не делай `SELECT` перед `INSERT` для проверки уникальности. `BaseRepository.add()` ловит `UniqueViolationError` и бросает `ObjectAlreadyExistsException`:

```python
# Правильно — ловим IntegrityError на уровне repository
await db.hotels.add(hotel_data)  # Бросит ObjectAlreadyExistsException

# Неправильно — TOCTOU race condition
existing = await db.hotels.get_one_or_none(title=data.title)
if existing:
    raise ...
```

### FK проверка перед удалением

Не парсь строку `IntegrityError`. Считай зависимые строки:

```python
# В сервисе:
count = await db.rooms.count_by_hotel(hotel_id)
if count > 0:
    raise CannotDeleteHotelWithRoomsException()
await db.hotels.delete(id=hotel_id)
```

### Доступность номеров — CTE запрос

`rooms_ids_for_booking()` в `src/repositories/utils.py` — ключевой SQL-запрос:

1. CTE `rooms_count` — считает пересекающиеся бронирования по каждому номеру
2. CTE `rooms_left_table` — `quantity - booked_count`
3. Результат — ID номеров где `rooms_left > 0`

Используется в `GET /hotels` (фильтрация) и `POST /bookings` (проверка доступности).

### Конкурентное бронирование

`BookingsRepository.add_booking()` использует `SELECT ... FOR UPDATE` на строке номера:

```
Transaction A: SELECT room WHERE id=5 FOR UPDATE  → lock acquired
Transaction B: SELECT room WHERE id=5 FOR UPDATE  → waits...
Transaction A: INSERT booking, COMMIT              → lock released
Transaction B: wakes up, re-checks availability    → может быть отказ
```

Никогда не убирай этот lock — без него возможен overbooking.

### RBAC

`is_admin` встроен в JWT payload при логине. `AdminDep` читает из токена — **без дополнительного запроса в БД**.

```python
# Все write-операции на hotels/rooms/facilities/images:
@router.post("/hotels")
async def create_hotel(admin_id: AdminDep, db: DBDep, data: HotelAdd):
    ...
```

### Кэширование

`fastapi-cache2` с Redis backend. Правила:

- `@cache(expire=N)` — только на GET-эндпоинтах без user-specific данных
- **Никогда** на `/bookings/me`, `/auth/me` — ключ кэша = URL, все юзеры получат одинаковый ответ
- После POST на `/facilities` — `FastAPICache.clear()`

---

## 7. Celery задачи

### Конфигурация

**Broker:** Redis (`settings.REDIS_URL`)

| Задача | Расписание | Retries | Описание |
|--------|-----------|---------|----------|
| `resize_image` | По вызову | 3 (60s delay) | Создаёт версии 1000/500/200px |
| `send_checkin_email` | По вызову | 3 (60s delay) | Отправляет одно email уведомление |
| `booking_today_checkin` | 08:00 UTC daily | - | Ищет заезды сегодня, вызывает `send_checkin_email` |
| `backup_database` | 03:00 UTC daily | 2 (300s delay) | `pg_dump | gzip`, чистка старых |

### Worker параметры (production)

```bash
celery worker --concurrency=2 --max-tasks-per-child=50 --max-memory-per-child=400000
```

- `--concurrency=2` — 2 процесса (по умолчанию = кол-во CPU, что на 10-ядерном сервере = 10 x 400MB)
- `--max-tasks-per-child=50` — рециклирование после 50 задач
- `--max-memory-per-child=400000` — рециклирование при 400MB RSS

---

## 8. Тестирование

### Запуск

```bash
uv run pytest -v                                    # Все тесты
uv run pytest tests/unit_tests -v                   # Только unit
uv run pytest tests/integration_tests -v            # Только integration
uv run pytest tests/integration_tests/auth/ -v      # Конкретная папка
uv run pytest -k "test_register" -v                 # По имени
uv run pytest --cov=src --cov-report=html           # С покрытием
```

### Требования

- PostgreSQL с базой `test` (создать заранее)
- Redis на `localhost:6379`
- Файл `.env-test` с `MODE=TEST` и `AUTH_RATE_LIMIT=1000/minute`

### Структура

```
tests/
├── conftest.py          # Session fixtures: DB setup, clients, auth
├── mock_hotels.json     # Тестовые данные отелей
├── mock_rooms.json      # Тестовые данные номеров
├── unit_tests/          # Валидация, JWT, схемы (без БД)
└── integration_tests/   # API через httpx.AsyncClient
    ├── auth/            # Регистрация, логин, RBAC, refresh, email
    ├── hotels/          # CRUD отелей
    ├── rooms/           # CRUD номеров
    ├── bookings/        # Бронирования
    ├── facilities/      # Удобства
    ├── middleware/       # Rate limit, CORS
    ├── test_health.py   # Health checks
    ├── test_metrics.py  # Prometheus metrics
    └── test_images.py   # Загрузка изображений
```

### Ключевые fixtures (conftest.py)

| Fixture | Scope | Описание |
|---------|-------|----------|
| `setup_database` | session | Drop all → create all → load mock data |
| `ac` | session | AsyncClient с cookies (persistent) |
| `unauth_ac` | function | AsyncClient без cookies |
| `authenticated_ac` | session | Авторизованный клиент |
| `admin_ac` | session | Клиент с `is_admin=True` |
| `db` | function | DBManager с NullPool |

### Частые причины падения тестов

| Симптом | Причина |
|---------|---------|
| Connection refused на всех тестах | PostgreSQL не запущен |
| JWT blacklist тесты падают | Redis не запущен |
| `AssertionError` на старте сессии | `MODE` не `TEST` в `.env-test` |
| 429 на auth тестах | `AUTH_RATE_LIMIT` слишком низкий |

---

## 9. Миграции (Alembic)

### Основные команды

```bash
# Применить все миграции
uv run alembic upgrade head

# Создать миграцию (autogenerate)
uv run alembic revision --autogenerate -m "add_field_to_table"

# Пустая миграция (для ручных изменений)
uv run alembic revision -m "custom_change"

# Откатить на одну версию назад
uv run alembic downgrade -1

# Текущая версия
uv run alembic current

# История
uv run alembic history --verbose
```

### Правила

- Новые модели **обязательно** добавлять в `src/models/__init__.py` (для autogenerate)
- Файлы миграций — `src/migrations/versions/`
- Формат имён: `YYYY_MM_DD_HHMM-<revision>_<slug>.py`
- Все настройки — в `src/config.py` (`Settings`), **не** хардкодить в миграциях

---

## 10. Мониторинг и observability

### Стек

```
Приложение → Prometheus (метрики, 90 дней)
           → Loki (логи, 7 дней) ← Promtail (сбор из Docker)
           → Tempo (трейсы, 7 дней) ← OpenTelemetry
           → Grafana (дашборды + алерты → Telegram / Email)
```

### Exporters

| Exporter | Порт | Что собирает |
|----------|------|-------------|
| node_exporter | 9100 | CPU, RAM, диск, сеть хоста |
| postgres_exporter | 9187 | Connections, query duration, cache hit |
| redis_exporter | 9121 | Memory, ops/sec, evictions |
| celery_exporter | 9808 | Workers, queue length, task counts |
| cAdvisor | 8080 | CPU/memory/IO контейнеров |
| blackbox_exporter | 9115 | HTTP probes (health, hotels) |

### Бизнес-метрики (Prometheus)

| Метрика | Тип | Где инкрементируется |
|---------|-----|---------------------|
| `hotel_booking_bookings_created_total` | Counter | `POST /bookings` (успех) |
| `hotel_booking_bookings_cancelled_total` | Counter | `DELETE /bookings/{id}` |
| `hotel_booking_booking_failed_total` | Counter | `POST /bookings` (нет мест / номер не найден) |
| `hotel_booking_search_requests_total` | Counter | `GET /hotels` |

### Алерты (16 правил)

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

### Дашборд

`grafana/provisioning/dashboards/hotel-booking.json` — автоматически загружается через file provisioning. Панели:

- RPS, Error Rate, Latency percentiles (p50/p95/p99)
- SLO Status (Availability), Error Budget Remaining (30d)
- Container CPU/Memory (агрегация `sum by (name)` для multi-core)
- DB Connections, Max Active TX Duration
- Celery Workers, Queue Length, Active Tasks
- Log of All FastAPI App (Loki)
- Deploy annotations

### Логирование

Structured JSON logs (`src/logging_config.py`) с полями:
- `trace_id` — корреляция с трейсами (Tempo)
- `request_id` — X-Request-ID header
- `level` — INFO/WARNING/ERROR (Loki label для фильтрации)

---

## 11. Docker и деплой

### Сервисы docker-compose

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

### Network

```bash
# Создать перед первым запуском
docker network create myNetwork
```

Все контейнеры — в `myNetwork` (external). Между собой обращаются по container_name.

### Volumes (persistent)

| Volume | Данные | Retention |
|--------|--------|-----------|
| prometheusdata | Метрики | 90 дней |
| grafanadata | Дашборды, плагины | - |
| lokidata | Логи | 7 дней |
| tempodata | Трейсы | 7 дней |
| imagesdata | Загруженные изображения | - |

### Деплой

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

### Особенности production (Linux)

- `extra_hosts: ["host.docker.internal:host-gateway"]` — обязательно для контейнеров, обращающихся к хосту
- Loki (`grafana/loki:latest` v3.x) — distroless, **нет** shell/wget/curl → healthcheck невозможен
- Grafana alerting file provisioning: `muteTimes:` и `policies:` **в разных файлах** (иначе ошибка валидации)
- Доступ к мониторингу — только через SSH tunnel, порты **не** открыты наружу

### SSH tunnel доступ

```bash
# Подключение с автоматическим проброском портов
ssh nas
# localhost:15432 → PostgreSQL
# localhost:16379 → Redis
# localhost:13000 → Grafana
```

---

## 12. Переменные окружения

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

---

## 13. Частые вопросы (FAQ)

### Как добавить новый endpoint?

1. Создай роутер в `src/api/` (или добавь в существующий)
2. Создай/обнови сервис в `src/services/`
3. Создай/обнови репозиторий в `src/repositories/` (если нужен новый запрос)
4. Добавь Pydantic схемы в `src/schemas/`
5. Добавь domain-исключение в `src/exceptions.py` + HTTP-исключение
6. Зарегистрируй роутер в `src/main.py`

### Как добавить новую модель?

1. Создай модель в `src/models/`
2. Добавь import в `src/models/__init__.py`
3. Создай миграцию: `uv run alembic revision --autogenerate -m "add_model_name"`
4. Примени: `uv run alembic upgrade head`
5. Создай репозиторий, маппер, схемы

### Как добавить Prometheus метрику?

1. Определи Counter/Gauge/Histogram в `src/middleware/prometheus.py`
2. Импортируй и инкрементируй в нужном месте (`src/api/*.py`)
3. Метрика автоматически появится на `/metrics`

### Почему на Grafana сервера "No data"?

- **SLO/Error Budget:** если нет 5xx-ответов, запрос возвращает пустую серию. Используй `or vector(0)` в числителе
- **Container метрики:** на multi-core сервере cAdvisor создаёт серию на каждый CPU core. Используй `sum(...) by (name)`
- **Prometheus только запустился:** метрикам нужно время для накопления (rate требует минимум 2 scrape)

### Почему контейнер перезапускается (Restarting)?

- `booking_back`: проверь `docker logs booking_back` — обычно `socket.gaierror` (DNS) или проблемы с БД
- `grafana`: проверь `docker logs grafana` — обычно ошибка в alerting provisioning файлах
- `loki`: если healthcheck unhealthy — это ложный отказ (distroless image, нет shell)

### Как подключиться к production БД?

```bash
ssh nas  # Автоматически пробрасывает порты
# DBeaver: localhost:15432, логин/пароль из .env
```

### Почему `docker restart` не помогает?

`docker restart` не перечитывает `docker-compose.yml`. Если менялись env vars, volumes или command — используй `docker compose up -d --no-deps <service>`.

### Как добавить алерт?

1. Добавь правило в `grafana/alerting/alert-rules.yaml`
2. Помни: `absent()` + `noDataState: Alerting` для "сервис не отвечает"; `noDataState: OK` для "метрика пропала потому что всё хорошо"
3. `docker compose up -d --no-deps grafana` для применения

### Как не потерять данные при обновлении?

Все данные в named volumes: `prometheusdata`, `grafanadata`, `lokidata`, `tempodata`, `imagesdata`. `docker compose down` **не** удаляет volumes. `docker compose down -v` — **удаляет** (не делай без необходимости).
