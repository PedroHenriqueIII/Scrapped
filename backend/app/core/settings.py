import os
from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    APP_NAME: str = "Scrapped"
    DEBUG: bool = True
    SECRET_KEY: str = "change-me-in-production"

    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/scrapped"

    REDIS_URL: str = "redis://localhost:6379/0"

    JWT_SECRET_KEY: str = "jwt-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60

    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/auth/callback"

    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    LINKEDIN_COOKIE_LI_AT: str = ""

    CNPJ_DB_PATH: str = "../data/cnpj.db"

    SPACY_MODEL: str = "pt_core_news_lg"
    SENTENCE_TRANSFORMER_MODEL: str = "paraphrase-multilingual-mpnet-base-v2"


@lru_cache
def get_settings() -> Settings:
    return Settings()