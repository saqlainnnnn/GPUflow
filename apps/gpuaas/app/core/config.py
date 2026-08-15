from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    environment: str = "development"

    postgres_host: str = "localhost"
    postgres_port: int = 5433
    postgres_user: str = "gpuflow"
    postgres_password: str = "gpuflow"
    postgres_db: str = "gpuflow"

    redis_host: str = "localhost"
    redis_port: int = 6379

    integration_hub_base_url: str = "http://localhost:8000"

    xero_client_id: str = ""
    xero_client_secret: str = ""
    xero_redirect_uri: str = "http://localhost:8001/api/v1/xero/callback"
    xero_scopes: str = "openid profile email accounting.invoices offline_access"
    xero_sales_account_code: str = "400"

    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"

    @property
    def database_url(self) -> str:
        return (
            "postgresql+asyncpg://"
            f"{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}"
            f"/{self.postgres_db}"
        )

    @property
    def sync_database_url(self) -> str:
        return (
            "postgresql+psycopg://"
            f"{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}"
            f"/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/0"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()