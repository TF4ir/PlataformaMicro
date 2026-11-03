"""Central application settings and environment configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    DATABASE_URL: str = "postgresql://postgres:postgres@127.0.0.1:5432/plataformamicro_test"
    SUPABASE_URL: str = "http://localhost:54321"
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    SUPABASE_JWT_SECRET: str = ""
    DEFAULT_LEASE_DURATION_SECONDS: int = 300
    MAX_JOB_ATTEMPTS: int = 3
    REPOSITORY_BACKEND: str = "postgres"  # "postgres" | "memory"
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000,https://plataformamicro.edu.pe"


settings = Settings()
