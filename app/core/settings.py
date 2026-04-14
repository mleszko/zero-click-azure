from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_env: str = Field(default='development', alias='APP_ENV')
    log_level: str = Field(default='INFO', alias='LOG_LEVEL')
    max_correction_loops: int = Field(default=3, alias='MAX_CORRECTION_LOOPS', ge=1, le=10)
    default_model_name: str = Field(default='rule-based-correction-graph', alias='DEFAULT_MODEL_NAME')

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore',
        case_sensitive=False,
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
