"""Runtime settings. Missing secrets are OK when MOCK_MODE=true."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    mock_mode: bool = True
    default_csm_id: str = "csm_demo_001"
    agent_host: str = "0.0.0.0"
    agent_port: int = 8000
    web_origin: str = "http://localhost:3000"

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-20250514"

    singlestore_host: str = ""
    singlestore_port: int = 3306
    singlestore_user: str = ""
    singlestore_password: str = ""
    singlestore_database: str = "nudge"

    sie_api_key: str = ""
    sie_base_url: str = "https://api.superlinked.com"
    sie_embed_model: str = "Qwen/Qwen3-Embedding-4B"
    sie_rerank_model: str = "Qwen/Qwen3-Reranker-4B"
    sie_classify_model: str = "knowledgator/gliclass-large-v3.0"
    sie_extract_model: str = "fastino/gliner2-large-v1"
    sie_redact_model: str = "numind/NuNER_Zero"

    amplitude_api_key: str = ""
    amplitude_secret_key: str = ""
    amplitude_api_url: str = "https://api2.amplitude.com/2/httpapi"

    hubspot_access_token: str = ""
    hubspot_base_url: str = "https://api.hubapi.com"
    stripe_secret_key: str = ""
    stripe_base_url: str = "https://api.stripe.com"
    gmail_base_url: str = "https://gmail.googleapis.com"
    slack_bot_token: str = ""
    slack_base_url: str = "https://slack.com/api"

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "nudge"
    postgres_password: str = "nudge"
    postgres_db: str = "nudge_support"


@lru_cache
def get_settings() -> Settings:
    return Settings()
