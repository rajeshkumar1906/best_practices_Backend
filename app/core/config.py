from functools import lru_cache
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Database
    DATABASE_URL: str = Field(default="sqlite:///./auth.db")
    TEST_DATABASE_URL: Optional[str] = Field(default="sqlite:///./test_auth.db")

    # JWT
    JWT_SECRET_KEY: str = Field(default="")
    JWT_ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60)

    # CORS
    CORS_ORIGINS: List[str] = Field(default_factory=lambda: ["http://localhost:3000", "http://10.0.2.2:8000"])

    # App
    APP_NAME: str = Field(default="Auth API")
    APP_VERSION: str = Field(default="1.0.0")
    DEBUG: bool = Field(default=False)


@lru_cache
def get_settings() -> Settings:
    return Settings()