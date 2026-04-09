# Developer Guide — Hotel Booking API

Документация для разработчиков. Обновляется по мере развития проекта.

---

## Содержание

| Документ | Описание |
|----------|----------|
| [Быстрый старт](getting-started.md) | Установка, запуск, первая проверка |
| [Архитектура](architecture.md) | Слои, структура проекта, модели, схемы, паттерны кода |
| [API Endpoints](api.md) | Все HTTP endpoints: auth, hotels, rooms, bookings, facilities, images, health |
| [Celery задачи](celery.md) | Фоновые задачи: resize, email, backup, worker параметры |
| [Тестирование](testing.md) | Запуск тестов, структура, fixtures, паттерны, покрытие |
| [Миграции](migrations.md) | Alembic команды и правила |
| [Мониторинг](observability.md) | Prometheus, Grafana, Loki, Tempo, алерты, дашборды |
| [Docker и деплой](deployment.md) | Сервисы, volumes, SSH tunnel, переменные окружения |
| [FAQ](faq.md) | Частые вопросы и решения типичных проблем |
| [Runbooks](runbooks.md) | Действия при срабатывании алертов (18 сценариев) |
