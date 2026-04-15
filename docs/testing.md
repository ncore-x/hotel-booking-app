# Тестирование

## Запуск

```bash
uv run pytest -v                                    # Все тесты
uv run pytest tests/unit_tests -v                   # Только unit
uv run pytest tests/integration_tests -v            # Только integration
uv run pytest tests/integration_tests/auth/ -v      # Конкретная папка
uv run pytest -k "test_register" -v                 # По имени
uv run pytest --cov=src --cov-report=html           # С покрытием
```

## Требования

- PostgreSQL с базой `test` (создать заранее)
- Redis на `localhost:6379`
- Файл `.env-test` с `MODE=TEST` и `AUTH_RATE_LIMIT=1000/minute`

## Структура

```
tests/
├── conftest.py          # Session fixtures: DB setup, clients, auth
├── mock_hotels.json     # Тестовые данные отелей
├── mock_rooms.json      # Тестовые данные номеров
├── unit_tests/          # Service layer, tasks, elastic, auth, logging (мокированные, без БД)
│   ├── test_auth_service.py     # AuthService (35 тестов)
│   ├── test_services.py         # Booking/Facility/Hotel/Room/Images services (62 теста)
│   ├── test_tasks.py            # Celery tasks: resize, email (14 тестов)
│   ├── test_elastic_client.py   # ES клиент (7 тестов)
│   ├── test_elastic_hotels.py   # ES индексация/поиск (9 тестов)
│   ├── test_exception_handlers.py # Обработчики ошибок (12 тестов)
│   ├── test_logging_config.py   # JSON логирование (7 тестов)
│   ├── test_token_blacklist.py  # Redis blacklist (7 тестов)
│   ├── test_redis_connector.py  # Redis connector (10 тестов)
│   ├── test_confirmation_service.py # ConfirmationService: create/consume token (12 тестов)
│   ├── test_oauth_service.py        # OAuthService: authorize URL, callback (14 тестов)
│   └── test_tracing.py          # OpenTelemetry (1 тест)
└── integration_tests/   # API через httpx.AsyncClient
    ├── auth/            # Регистрация, логин, RBAC, refresh, email
    │   ├── test_confirmation.py     # GET /auth/confirm?token= (5 тестов)
    │   └── test_oauth.py            # OAuth authorize + callback (8 тестов)
    ├── hotels/          # CRUD отелей
    ├── rooms/           # CRUD номеров
    ├── bookings/        # Бронирования
    ├── facilities/      # Удобства
    ├── middleware/       # Rate limit, CORS
    ├── test_health.py   # Health checks
    ├── test_metrics.py  # Prometheus metrics
    └── test_images.py   # Загрузка изображений
```

## Ключевые fixtures (conftest.py)

| Fixture | Scope | Описание |
|---------|-------|----------|
| `setup_database` | session | Drop all → create all → load mock data |
| `ac` | session | AsyncClient с cookies (persistent) |
| `unauth_ac` | function | AsyncClient без cookies |
| `authenticated_ac` | session | Авторизованный клиент |
| `admin_ac` | session | Клиент с `is_admin=True` |
| `db` | function | DBManager с NullPool |

## Частые причины падения тестов

| Симптом | Причина |
|---------|---------|
| Connection refused на всех тестах | PostgreSQL не запущен |
| JWT blacklist тесты падают | Redis не запущен |
| `AssertionError` на старте сессии | `MODE` не `TEST` в `.env-test` |
| 429 на auth тестах | `AUTH_RATE_LIMIT` слишком низкий |

## Паттерны тестирования

- **Celery tasks**: `task._orig_run()` для вызова оригинальной функции, минуя `bind=True` + `autoretry_for`
- **Lazy settings imports**: Патчить `src.config.settings`, а не локальную ссылку в модуле
- **AsyncMock для `async with`**: `mock_ctx.__aenter__.return_value = mock_inner`
- **Pydantic validators**: Выполняются до service-логики — тестировать границы валидатора отдельно
- **ES fallback**: Патчить `get_es_client` → `None` (отключён) или `AsyncMock()` (включён)
- **Cache**: Патчится целиком: `mock.patch("fastapi_cache.decorator.cache", lambda *args, **kwargs: lambda f: f)`
- **NullPool**: Использовать `engine_null_pool` в тестах — избегает asyncio pool issues
- **Capture confirmation token**: патчить `ConfirmationService.create_token` для захвата токена без прямого обращения к Redis — прямые `redis_manager.redis.keys()` вызовы ломают pool при session event loop
- **OAuth state via HTTP**: вызывать `GET /auth/oauth/google/authorize` через ASGI, извлекать state из URL — не писать state напрямую в Redis из тестов
- **asyncio loop scope**: в `pytest.ini` обязательны оба ключа: `asyncio_default_fixture_loop_scope = session` и `asyncio_default_test_loop_scope = session`

## Текущий статус

413 тестов, 86%+ покрытие (апрель 2026).

### Покрытие по слоям

- Services: 90-100% (все сервисы на 100%, кроме images 90%, auth 98%)
- Schemas/Models: 94-100%
- Tasks: 85%
- Elastic: 100%
- Repositories: 55-82% (тестируются косвенно через интеграционные тесты)
- API routers: 51-82% (тестируются через интеграционные тесты)
