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
    enable_azure_openai: bool = Field(default=False, alias='ENABLE_AZURE_OPENAI')
    azure_openai_endpoint: str | None = Field(default=None, alias='AZURE_OPENAI_ENDPOINT')
    azure_openai_api_version: str = Field(default='2024-06-01', alias='AZURE_OPENAI_API_VERSION')
    azure_openai_deployment: str | None = Field(default=None, alias='AZURE_OPENAI_DEPLOYMENT')
    azure_openai_managed_identity_client_id: str | None = Field(
        default=None,
        alias='AZURE_OPENAI_MANAGED_IDENTITY_CLIENT_ID',
    )

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore',
        case_sensitive=False,
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
