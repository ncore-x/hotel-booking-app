# Архитектура

## Слои (сверху вниз)

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

## Ключевые принципы

- **Service никогда не бросает HTTPException** — только domain-исключения из `src/exceptions.py`
- **API-слой ловит domain-исключения и переводит в HTTP** — `except HotelNotFoundException: raise HotelNotFoundHTTPException()`
- **Один DBManager на запрос** — все репозитории делят одну сессию (Unit of Work)
- **Commit явный** — `await db.commit()` вызывается в сервисе, rollback автоматический

---

## Структура проекта

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
│   ├── hotels.py               # hotels (title, city, address) + UNIQUE constraint
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

## Модели и схемы

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
  ├── id (PK), title, city, address
  ├── UNIQUE(title, city, address) — uq_hotels_title_city_address
  ├── GIN INDEX(title, city) — pg_trgm для поиска
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

## Паттерны кода

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
