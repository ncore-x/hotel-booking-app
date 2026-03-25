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
    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    # Cookie
    COOKIE_SECURE: bool = False  # True на HTTPS (продакшн)

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

    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}"

    @property
    def DB_URL(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()  # type: ignore
