from pathlib import Path
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    MODE: Literal["TEST", "LOCAL", "DEV", "PROD"]

    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASS: str
    DB_NAME: str

    REDIS_HOST: str
    REDIS_PORT: int

    JWT_SECRET_KEY: str
    JWT_SECRET_KEY_PREVIOUS: str | None = None  # для ротации: старый ключ остаётся валидным
    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Cookie
    COOKIE_SECURE: bool = False  # True на HTTPS (продакшн)

    # Database connection pool
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30  # seconds to wait for a connection from the pool

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # Rate limiting
    AUTH_RATE_LIMIT: str = "10/minute"  # формат slowapi: "N/unit"

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_JSON: bool = False  # True на продакшне

    # Images
    IMAGES_DIR: Path = Path("src/static/images")
    MAX_IMAGE_SIZE_BYTES: int = 5_242_880  # 5 MB

    # SMTP (опционально — если не задано, письма только логируются)
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM: str = "noreply@hotelbooking.example"

    # Sentry (опционально — если не задано, Sentry не инициализируется)
    SENTRY_DSN: str | None = None
    SENTRY_ENVIRONMENT: str = "local"
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1  # 10% трейсов в продакшене

    # Database backups
    BACKUP_DIR: Path = Path("backups")
    BACKUP_RETAIN_DAYS: int = 7

    # Metrics
    METRICS_ENABLED: bool = True
    METRICS_TOKEN: str | None = None  # если задан — /metrics требует Authorization: Bearer <token>

    # Tracing (OpenTelemetry → Tempo)
    OTEL_ENABLED: bool = False
    OTEL_ENDPOINT: str = "http://tempo:4317"  # gRPC endpoint
    OTEL_SERVICE_NAME: str = "hotel_booking"

    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}"

    @property
    def DB_URL(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()  # type: ignore
