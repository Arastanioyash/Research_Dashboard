from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="RD_", env_file=".env", extra="ignore")

    app_name: str = "Research Dashboard API"
    app_version: str = "0.1.0"
    api_prefix: str = "/api/v1"
    log_level: str = "INFO"

    secret_key: str = "change-me"
    access_token_expire_minutes: int = 60

    data_root: str = "data/projects"
    user_db_path: str = "data/users.sqlite"


@lru_cache
def get_settings() -> Settings:
    return Settings()
