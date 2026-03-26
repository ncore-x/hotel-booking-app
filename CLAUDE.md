# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

**Package manager:** `uv` (not pip/poetry).

```bash
# Run dev server
uv run uvicorn src.main:app --reload

# Run all tests
uv run pytest tests/

# Run a single test file
uv run pytest tests/integration_tests/hotels/test_api.py

# Run a single test by name
uv run pytest tests/integration_tests/hotels/test_api.py::test_get_hotels

# Lint
uv run ruff check src/ tests/

# Format (CI uses ruff, not black)
uv run ruff format src/ tests/

# Migrations (run from project root)
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "description"

# Celery worker
uv run celery -A src.tasks.celery_app:celery_instance worker --loglevel=info

# Celery beat scheduler
uv run celery -A src.tasks.celery_app:celery_instance beat --loglevel=info
```

Tests use a separate `.env-test` file. `settings.MODE` must equal `"TEST"` — the conftest asserts this at session start. Tests run against a real test database (not mocked). The test suite drops and recreates all tables on each session via `Base.metadata`.

`AUTH_RATE_LIMIT=1000/minute` must be set in `.env-test` to prevent tests from hitting the rate limiter.

**Common test failure causes:**
- PostgreSQL not running → connection refused on all tests
- Redis not running → JWT blacklist tests fail (graceful fallback exists, but some tests assert Redis behaviour)
- `MODE` missing or not `TEST` → conftest aborts entire session with `AssertionError`
- `AUTH_RATE_LIMIT` too low → auth tests hit 429

## Claude Code Configuration

### Permissions (`~/.claude/settings.json`, global)

Commands allowed without confirmation: `uv *`, `alembic *`, `ruff *`, `git status *`, `git diff *`, `git log *`.

### Pre-commit hook (`.claude/settings.json`, project)

`PreToolUse → Bash` hook fires on any `git commit` command. Runs `uv run ruff format src/ tests/ && uv run ruff check src/ tests/` automatically. Blocks the commit if ruff fails.

### Skills (`.claude/skills/`)

- `/go` — orchestrator, use before any non-trivial task
- `/pre-commit` — manual lint + format check
- `/new-endpoint` — step-by-step guide for adding a new endpoint
- `/fix-bugs` — list of known bugs with exact locations and fixes
- `/migrate` — Alembic migration workflow

---

## Architecture

**Layers (top → bottom):** `api/` → `services/` → `repositories/` → SQLAlchemy ORM models

### Request flow

1. **`src/api/*.py`** — FastAPI routers. Translate domain exceptions into HTTP exceptions. Do not contain business logic.
2. **`src/services/*.py`** — Business logic. Raise domain exceptions (from `src/exceptions.py`), never `HTTPException`. Accept `DBManager` as dependency.
3. **`src/repositories/*.py`** — Database access. One repository per ORM model, all extend `BaseRepository`. Return domain Pydantic schemas via DataMapper.
4. **`src/repositories/mappers/`** — `DataMapper.map_to_domain_entity()` converts ORM objects to Pydantic schemas via `model_validate(..., from_attributes=True)`.

### Unit of Work — `DBManager`

`src/utils/db_manager.py` is an async context manager used as a Unit of Work. All repositories share one SQLAlchemy session per request. Commit explicitly with `await db.commit()`; rollback happens automatically on `__aexit__`. Injected into services via `DBDep = Annotated[DBManager, Depends(get_db)]`.

Two engines exist: `engine` (with connection pool, for the app) and `engine_null_pool` (for Celery tasks and tests, avoids pool issues with asyncio). Always use `engine_null_pool` in health checks and Celery tasks.

### Exceptions pattern

Two parallel exception hierarchies in `src/exceptions.py`:
- **Domain exceptions** (`NabronirovalException` subclasses) — raised by services and repositories.
- **HTTP exceptions** (`NabronirovalHTTPException` subclasses) — raised by API routers after catching domain exceptions.

Services must never raise HTTP exceptions. API routers catch domain exceptions and re-raise the corresponding HTTP exception.

### Schemas

- `*AddRequest` / `*PatchRequest` — what the API receives from the client (with validation).
- `*Add` / `*Patch` — what the repository writes to the DB (includes computed fields like `hotel_id`, `user_id`, `price`).
- `*` (e.g. `Hotel`, `Room`, `Booking`) — what the repository returns (includes `id`).

Validators in schemas raise `ValueError` with Russian messages — never `HTTPException`.

### Availability query

`src/repositories/utils.py::rooms_ids_for_booking()` is the core SQL query for hotel/room availability. It uses two CTEs: `rooms_count` (bookings in the date range) and `rooms_left_table` (quantity minus booked). Used by both `HotelsRepository.get_filtered_by_time` and `BookingsRepository.add_booking`.

### Concurrency — booking race condition

`BookingsRepository.add_booking` uses `SELECT ... FOR UPDATE` on the room row before checking availability. This serialises concurrent booking attempts for the same room: the second transaction waits for the first to commit, then re-checks the (now updated) availability count. Never remove this lock.

### Duplicate detection

Hotels have a DB-level unique constraint `uq_hotels_title_location` on `(title, location)`. Facilities have a unique constraint `uq_facilities_title` on `title`. Do **not** add a manual SELECT-before-INSERT check — rely on `BaseRepository.add()` catching `UniqueViolationError` → `ObjectAlreadyExistsException`. Same pattern applies to `BaseRepository.edit()` which also catches `UniqueViolationError`.

### FK constraint checks before delete

Do **not** catch `IntegrityError` and parse its message string to detect FK violations — it is fragile. Instead, count dependent rows before deleting:
- `delete_hotel` → `rooms.count_by_hotel(hotel_id)` — raises `CannotDeleteHotelWithRoomsException` if > 0.
- `delete_room` → `bookings.count_by_room(room_id)` — raises `CannotDeleteRoomWithBookingsException` if > 0.

### Caching

`fastapi-cache2` with Redis backend. Applied at the router level with `@cache(expire=10)`. The conftest patches it out entirely for tests with `mock.patch("fastapi_cache.decorator.cache", lambda *args, **kwargs: lambda f: f)`.

**Never apply `@cache` to user-specific endpoints** (e.g. `/bookings/me`, `/auth/me`). The cache key is the URL — all users would share the same cached response.

### RBAC

`AdminDep = Annotated[int, Depends(get_current_admin)]` in `src/api/dependencies.py`. All write operations on hotels, rooms, facilities, and images require `AdminDep`. The dependency reads `is_admin` from the JWT payload — **no extra DB SELECT** per request. `is_admin` is embedded in the access token at login time.

JWT blacklist is managed by `TokenBlacklistService` (`src/services/token_blacklist.py`). On logout, both tokens are blacklisted with TTL = remaining lifetime. `get_current_user_id` calls `blacklist.is_blacklisted(token)` on every request. If Redis is down, the check is skipped gracefully (returns `False`).

### Pagination

`PaginatedResponse[T]` in `src/schemas/common.py` is the standard paginated response. Use it for all list endpoints. `has_next` and `has_prev` are `@computed_field` properties. Pattern:
```python
total = await self.db.repo.count_*(...)
items = await self.db.repo.get_*(limit=per_page, offset=per_page * (page - 1))
return PaginatedResponse(items=items, total=total, page=page, per_page=per_page,
                         pages=max(1, math.ceil(total / per_page)))
```

### Hotel images

Images are stored on disk (`settings.IMAGES_DIR`) and tracked in the `hotel_images` table (`src/models/hotel_images.py`). Endpoints are hotel-scoped:
- `POST /hotels/{hotel_id}/images` — admin only, saves file + DB record, triggers `resize_image` Celery task.
- `GET /hotels/{hotel_id}/images` — public, returns `list[HotelImage]`.

`HotelImageAdd` / `HotelImage` schemas live in `src/schemas/images.py`.

File I/O uses `asyncio.to_thread` — never blocking `open()` in async context. If the DB insert fails after the file is written, the file is deleted automatically (rollback on error).

### Background tasks

Celery with Redis as broker (`src/tasks/`). Three tasks:
- `resize_image` — creates 1000/500/200px versions of uploaded images, saves to `settings.IMAGES_DIR`. `autoretry_for=(Exception,)`, `max_retries=3`, `default_retry_delay=60`.
- `send_emails_to_users_with_today_checkin` — runs on beat schedule (`crontab(hour=8, minute=0)` UTC). Uses JOIN query `get_today_checkins_with_emails` — no N+1. Dispatches individual email tasks via `.delay()`. Never calls SMTP directly.
- `send_checkin_email` — isolated task: sends one check-in email via SMTP. `autoretry_for=(Exception,)`, `max_retries=3`. SMTP errors propagate (no swallowing) so retries fire.

Uses `datetime.now(tz=timezone.utc).date()` everywhere — never `date.today()`.

### Auth endpoints

- `POST /auth/register` — rate-limited (Redis-backed), returns 201 + `User`.
- `POST /auth/login` — rate-limited (Redis-backed), sets `access_token` + `refresh_token` cookies (`httponly`, `samesite=lax`, `secure=settings.COOKIE_SECURE`). Returns `LoginResponse` with both tokens.
- `GET /auth/me` — returns current user.
- `PATCH /auth/me` — change password (`UserPasswordUpdate`: `current_password` + `new_password`). Returns 204.
- `PATCH /auth/me/email` — change email (`UserEmailUpdate`: `new_email` + `current_password`). Verifies password, rejects same email (409), rejects taken email (409). Returns 204.
- `POST /auth/refresh` — validates `refresh_token` cookie, issues new `access_token`. Returns `LoginResponse`.
- `POST /auth/logout` — blacklists both `access_token` and `refresh_token` in Redis, clears both cookies.

### JWT token types

Access and refresh tokens are both JWTs signed with `JWT_SECRET_KEY`. They are distinguished by the `type` field in the payload:
- `type: "access"` — short-lived (`ACCESS_TOKEN_EXPIRE_MINUTES`). Required for all protected endpoints. `get_current_user_id` rejects tokens with any other type.
- `type: "refresh"` — long-lived (`REFRESH_TOKEN_EXPIRE_DAYS`, default 30 days). Only accepted by `POST /auth/refresh`.

**Key rotation:** set `JWT_SECRET_KEY_PREVIOUS` in `.env` to keep old tokens valid during rotation. `decode_token` tries the current key first, falls back to the previous key on `InvalidTokenError`.

### Booking endpoints

- `GET /bookings/me` — paginated (`PaginatedResponse[Booking]`), params `page`/`per_page`.
- `GET /bookings/{id}` — single booking (ownership-checked: returns 404 if not yours).
- `POST /bookings` — creates booking, uses `SELECT FOR UPDATE` internally.
- `PATCH /bookings/{id}` — updates dates. Atomically deletes old booking + re-books with new dates in one transaction; rolls back if new dates unavailable.
- `DELETE /bookings/{id}` — cancels booking.

## Key conventions

- All new settings go in `src/config.py` as `Settings` fields — never hardcode paths or limits.
- Alembic migrations live in `src/migrations/versions/`. The `env.py` reads `DB_URL` from `settings` and imports all models via `src/models/__init__.py` for autogenerate to work. New models must be added to `src/models/__init__.py`.
- `CORS` `allow_origins` must be a specific list — not `["*"]` — when `allow_credentials=True`.
- Middleware order in `main.py` matters: CORS must be added before `JSONErrorHandlerMiddleware`. `GZipMiddleware` is registered before both.
- `GZipMiddleware(minimum_size=1000)` compresses responses larger than 1KB — do not remove it.
- Use `datetime.now(tz=timezone.utc)` everywhere — never `datetime.now()` or `date.today()`.
- CI uses `ruff format --check` (not black) and `ruff check` on both `src/` and `tests/`. Always run `uv run ruff format src/ tests/ && uv run ruff check src/ tests/` before committing.

---

## Project status (as of 2026-03-26, commit a71f49d)

### What was implemented

**Security:**
- JWT blacklist via `TokenBlacklistService` (`src/services/token_blacklist.py`) — single responsibility, injected into `AuthService` and `get_current_user_id` via FastAPI `Depends`
- JWT key rotation: `JWT_SECRET_KEY_PREVIOUS` allows zero-downtime secret rotation
- Refresh token: `POST /auth/refresh`, long-lived JWT (`type: "refresh"`), blacklisted on logout
- Token type validation: `get_current_user_id` rejects non-`access` tokens (prevents refresh token misuse)
- `is_admin` embedded in JWT access token payload — `get_current_admin` reads from token, no extra DB SELECT
- RBAC: `is_admin` field in `users` table, `AdminDep` dependency — all hotel/room/facility/image writes require admin (403 otherwise)
- Cookie hardening: `httponly`, `samesite=lax`, `COOKIE_SECURE` setting
- Rate limiting via slowapi with Redis storage (shared across workers) on `/register` and `/login`
- `SELECT FOR UPDATE` in `add_booking` to prevent overbooking race condition
- `uq_hotels_title_location` DB unique constraint on `(title, location)`
- `uq_facilities_title` DB unique constraint on `title`
- FK violations detected via count query before delete

**Endpoints:**
- `GET /health` — checks DB + Redis, returns 200/503
- `POST /auth/refresh` — issues new access token from refresh token cookie
- `GET /bookings/{id}` — single booking, ownership-checked
- `PATCH /bookings/{id}` — change dates atomically
- `PATCH /auth/me` — change password
- `POST /hotels/{hotel_id}/images` — admin only; saves to disk + DB; triggers `resize_image` Celery task
- `GET /hotels/{hotel_id}/images` — public

**Infrastructure:**
- `PaginatedResponse[T]` in `src/schemas/common.py` — all list endpoints use it
- `GZipMiddleware(minimum_size=1000)` — response compression
- SQLAlchemy connection pool tuning: `pool_size`, `max_overflow`, `pool_timeout`, `pool_pre_ping` from Settings
- JSON structured logging (`src/logging_config.py`); controlled by `LOG_LEVEL` / `LOG_JSON` settings
- `RequestIDMiddleware` — adds `X-Request-ID` to every request/response
- Redis-backed slowapi storage — rate limit counters shared across all workers
- `send_checkin_email` isolated as separate Celery task — SMTP no longer blocks scheduler; `autoretry_for=(Exception,)`, `max_retries=3`
- `resize_image` Celery task: `autoretry_for=(Exception,)`, `max_retries=3`
- Celery beat: `crontab(hour=8, minute=0)` instead of raw `schedule=86400`
- `_get_bookings_and_notify` uses JOIN query — no N+1 on user emails
- HTML email template (multipart/alternative with plain text fallback)
- Redis graceful degradation: falls back to `InMemoryBackend` if Redis unavailable at startup
- Sentry: initialized on startup if `SENTRY_DSN` is set (`SENTRY_ENVIRONMENT`, `SENTRY_TRACES_SAMPLE_RATE`)
- `backup_database` Celery task: `pg_dump | gzip` → `BACKUP_DIR/backup_YYYYMMDD.sql.gz`, daily at 03:00 UTC, auto-cleanup after `BACKUP_RETAIN_DAYS` (default 7)
- `created_at` / `updated_at` on hotels, users, bookings, rooms models
- DB indexes: `bookings(user_id)`, `bookings(room_id)`, `bookings(date_from)`, `rooms(hotel_id)`, `hotel_images(hotel_id)`
- Trigram indexes on `hotels(title)` and `hotels(location)` via `pg_trgm` extension
- Async file I/O in `ImagesService` via `asyncio.to_thread`; file deleted on DB error (rollback)

**Tests:** 157 passed — RBAC, JWT blacklist, refresh token (5 cases), change email (6 cases), pagination, middleware, room CRUD, health, images, schema validators.

**CI/CD (GitLab pipeline):** build → lint_format → migrations → test → deploy.

---

## Known bugs

None.

## Known missing features

- **Prometheus metrics** — no `/metrics` endpoint; can't track latency/error rate in prod.
- **S3/MinIO for images** — images stored on local disk; breaks with multiple API instances.
