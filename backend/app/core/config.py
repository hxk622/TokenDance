"""
Application configuration using Pydantic Settings.
Supports multiple environments: development, staging, production.
"""
from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with validation."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Environment
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = False

    # API
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "TokenDance"
    VERSION: str = "0.1.0"

    # Security
    SECRET_KEY: str = Field(..., min_length=32)
    # Access token: 7 days (滑动窗口机制)
    ACCESS_TOKEN_EXPIRE_DAYS: int = 7
    # Refresh token: 30 days (用于长期离线后重新登录)
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    ALGORITHM: str = "HS256"

    # CORS - allow common dev ports
    BACKEND_CORS_ORIGINS: list[str] = Field(
        default=[
            "http://localhost:5173",
            "http://localhost:5174",
            "http://localhost:5175",
            "http://localhost:5176",
            "http://localhost:3000",
        ]
    )

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | list[str] | None) -> list[str]:
        default_origins = [
            "http://localhost:5173",
            "http://localhost:5174",
            "http://localhost:5175",
            "http://localhost:5176",
            "http://localhost:3000",
        ]
        if v is None:
            return default_origins
        if isinstance(v, str) and v:
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        if isinstance(v, list):
            return v
        return default_origins

    # Database
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "tokendance"
    POSTGRES_PASSWORD: str = ""  # Empty for local trust auth
    POSTGRES_DB: str = "tokendance"

    @property
    def DATABASE_URL(self) -> str:
        """Construct database URL."""
        return str(
            PostgresDsn.build(
                scheme="postgresql+asyncpg",
                username=self.POSTGRES_USER,
                password=self.POSTGRES_PASSWORD,
                host=self.POSTGRES_HOST,
                port=self.POSTGRES_PORT,
                path=self.POSTGRES_DB,
            )
        )

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str | None = None

    @property
    def REDIS_URL(self) -> str:
        """Construct Redis URL."""
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # FileSystem
    DATA_ROOT: str = "./data"
    WORKSPACE_ROOT_PATH: str = "./data/workspaces"

    # Object Storage (MinIO / S3 compatible)
    MINIO_ENDPOINT: str | None = None  # e.g. "localhost:9000"
    MINIO_ACCESS_KEY: str | None = None
    MINIO_SECRET_KEY: str | None = None
    MINIO_REGION: str | None = None
    MINIO_SECURE: bool = False
    MINIO_BUCKET_REPORTS: str = "research-reports"

    @property
    def USERS_DATA_PATH(self) -> str:
        """Path for personal user data."""
        return f"{self.DATA_ROOT}/users"

    @property
    def ORGS_DATA_PATH(self) -> str:
        """Path for organization data."""
        return f"{self.DATA_ROOT}/orgs"

    @property
    def SESSIONS_DATA_PATH(self) -> str:
        """Path for session working memory data."""
        return f"{self.WORKSPACE_ROOT_PATH}/sessions"

    # LLM (unified via OpenRouter)
    OPENROUTER_API_KEY: str | None = None
    # Default model - use deepseek for global availability (Claude may be region-restricted)
    DEFAULT_LLM_MODEL: str = "deepseek/deepseek-chat"
    MAX_CONTEXT_TOKENS: int = 128000

    # WeChat OAuth
    WECHAT_APP_ID: str | None = None
    WECHAT_APP_SECRET: str | None = None
    WECHAT_REDIRECT_URI: str = "http://localhost:5173/auth/wechat/callback"

    # Gmail OAuth
    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None
    GMAIL_REDIRECT_URI: str = "http://localhost:5173/auth/gmail/callback"
    GMAIL_SCOPES: str = "openid,profile,email"

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    # Monitoring
    ENABLE_METRICS: bool = True
    LOG_LEVEL: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
