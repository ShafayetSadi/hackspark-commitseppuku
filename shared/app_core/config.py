from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class CommonSettings(BaseSettings):
    project_name: str = "hackathon-microservices"
    app_env: str = "dev"
    log_level: str = "INFO"
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 120
    metrics_enabled: bool = True
    metrics_token: str | None = None
    postgres_user: str = "hackathon"
    postgres_password: str = "hackathon"
    postgres_db: str = "hackathon"
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    sqlite_path: str = "./service.db"
    database_backend: str = "postgresql"
    central_api_rate_limit: int = 20
    central_api_rate_window_seconds: float = 60.0
    central_api_redis_url: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def normalized_app_env(self) -> str:
        return self.app_env.strip().lower()

    @property
    def is_dev(self) -> bool:
        return self.normalized_app_env == "dev"

    @property
    def service_docs_enabled(self) -> bool:
        return self.is_dev

    @property
    def gateway_docs_enabled(self) -> bool:
        return self.is_dev

    @property
    def database_url(self) -> str:
        if self.database_backend == "sqlite":
            return f"sqlite+aiosqlite:///{self.sqlite_path}"
        return (
            "postgresql+asyncpg://"
            f"{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_common_settings() -> CommonSettings:
    return CommonSettings()
