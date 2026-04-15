# API Endpoints

## Auth (`/auth`)

| Метод | Endpoint | Описание | Auth | Rate limit |
|-------|----------|----------|------|------------|
| POST | `/auth/register` | Регистрация | - | AUTH_RATE_LIMIT |
| POST | `/auth/login` | Вход (устанавливает cookies) | - | AUTH_RATE_LIMIT |
| GET | `/auth/me` | Профиль текущего пользователя | JWT | - |
| PATCH | `/auth/me` | Инициировать смену пароля (отправляет письмо с подтверждением) | JWT | - |
| PATCH | `/auth/me/email` | Инициировать смену email (отправляет письмо с подтверждением) | JWT | - |
| GET | `/auth/confirm` | Применить смену пароля/email по токену из письма | - | - |
| GET | `/auth/oauth/{provider}/authorize` | Получить URL для OAuth авторизации (Google) | - | - |
| POST | `/auth/oauth/{provider}/callback` | Завершить OAuth вход, получить JWT cookies | - | - |
| POST | `/auth/refresh` | Обновить access token | refresh cookie | - |
| POST | `/auth/logout` | Blacklist токенов, очистка cookies | JWT | - |

**JWT:** Access token (короткоживущий) + Refresh token (30 дней). Оба в httponly cookies.
**Key rotation:** Если установлен `JWT_SECRET_KEY_PREVIOUS`, старые токены валидны.

**OAuth:** Поддерживается Google OAuth 2.0. Требует `GOOGLE_CLIENT_ID` и `GOOGLE_CLIENT_SECRET`.  
Флоу: `GET /authorize` → редирект на Google → `POST /callback?code=&state=` → JWT cookies.  
OAuth-пользователи не имеют пароля — `PATCH /auth/me` и `PATCH /auth/me/email` вернут 401.

**Confirmation flow:** `PATCH /auth/me` и `PATCH /auth/me/email` не применяют изменения сразу.  
Они создают одноразовый токен в Redis (TTL 1 час) и отправляют письмо со ссылкой.  
`GET /auth/confirm?token=` применяет изменение. Токен одноразовый — повторный запрос вернёт 400.

## Hotels (`/hotels`)

| Метод | Endpoint | Описание | Auth | Пагинация |
|-------|----------|----------|------|-----------|
| GET | `/hotels` | Список отелей (с фильтром по датам) | - | да |
| GET | `/hotels/{id}` | Один отель | - | - |
| POST | `/hotels` | Создать отель | Admin | - |
| PUT | `/hotels/{id}` | Полное обновление | Admin | - |
| PATCH | `/hotels/{id}` | Частичное обновление | Admin | - |
| DELETE | `/hotels/{id}` | Удалить (если нет номеров) | Admin | - |

**GET /hotels query params:** `date_from`, `date_to` (required), `city`, `title`, `sort_by`, `order`, `page`, `per_page`

## Rooms (`/hotels/{hotel_id}/rooms`)

| Метод | Endpoint | Описание | Auth |
|-------|----------|----------|------|
| GET | `/hotels/{id}/rooms` | Свободные номера в диапазоне дат | - |
| GET | `/hotels/{id}/rooms/{room_id}` | Один номер с удобствами | - |
| POST | `/hotels/{id}/rooms` | Создать номер | Admin |
| PUT | `/hotels/{id}/rooms/{room_id}` | Полное обновление | Admin |
| PATCH | `/hotels/{id}/rooms/{room_id}` | Частичное обновление | Admin |
| DELETE | `/hotels/{id}/rooms/{room_id}` | Удалить (если нет бронирований) | Admin |

## Bookings (`/bookings`)

| Метод | Endpoint | Описание | Auth |
|-------|----------|----------|------|
| GET | `/bookings/me` | Мои бронирования | JWT |
| GET | `/bookings/{id}` | Одно бронирование (проверка владельца) | JWT |
| POST | `/bookings` | Забронировать (с row lock) | JWT |
| PATCH | `/bookings/{id}` | Изменить даты (атомарно) | JWT |
| DELETE | `/bookings/{id}` | Отменить | JWT |

## Facilities (`/facilities`)

| Метод | Endpoint | Описание | Auth | Кэш |
|-------|----------|----------|------|-----|
| GET | `/facilities` | Список удобств | - | 300s |
| POST | `/facilities` | Создать удобство | Admin | clears cache |

## Images (`/hotels/{hotel_id}/images`)

| Метод | Endpoint | Описание | Auth |
|-------|----------|----------|------|
| POST | `/hotels/{id}/images` | Загрузить изображение (JPEG/PNG/WebP, max 5MB) | Admin |
| GET | `/hotels/{id}/images` | Список изображений отеля | - |

## Health (`/health`)

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/api/v1/health` | Полная проверка (DB + Redis) + version |
| GET | `/api/v1/health/live` | Liveness probe (200 OK) |

## Metrics

| Метод | Endpoint | Описание | Auth |
|-------|----------|----------|------|
| GET | `/metrics` | Prometheus метрики | Bearer (METRICS_TOKEN) |
