"""Central application settings and environment configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    DATABASE_URL: str = "postgresql://postgres:postgres@127.0.0.1:5432/plataformamicro_test"
    # AWS Secrets Manager integration for secure DSN resolution
    DATABASE_SECRET_ARN: str | None = None
    AWS_REGION: str = "us-east-2"
    SUPABASE_URL: str = "http://localhost:54321"
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    SUPABASE_JWT_SECRET: str = "super-secret-jwt-token-with-at-least-32-characters-long"
    # Optional override. Derived from SUPABASE_URL when empty:
    # {SUPABASE_URL}/auth/v1/.well-known/jwks.json
    SUPABASE_JWKS_URL: str = ""
    DEFAULT_LEASE_DURATION_SECONDS: int = 300
    MAX_JOB_ATTEMPTS: int = 3
    REPOSITORY_BACKEND: str = "postgres"  # "postgres" | "memory"
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000,https://plataformamicro.fabriziovalerio-c.workers.dev"
    ENABLE_CORS_MIDDLEWARE: bool = True
    CONTENT_GENERATION_WORKER_ENABLED: bool = True

    # Database connection pooling & Supavisor settings
    DB_POOL_MIN_SIZE: int = 1
    DB_POOL_MAX_SIZE: int = 5
    DB_POOL_MODE: str = "auto"  # "auto" | "session" | "transaction"
    DB_STATEMENT_CACHE_SIZE: int | None = None
    DB_SSL_MODE: str = "auto"  # "auto" | "require" | "disable"
    DB_COMMAND_TIMEOUT: float = 30.0
    DB_CONNECT_TIMEOUT: float = 10.0
    # Recycle idle/aged connections. Serverless environments (AWS Lambda)
    # freeze the event loop, so a short lifetime prevents reusing connections
    # that Supabase/Supavisor already closed while the environment was frozen.
    DB_MAX_INACTIVE_CONNECTION_LIFETIME: float = 300.0
    DB_MAX_QUERIES: int = 50000
    # Extra attempts for a stale connection after a Lambda thaw.
    DB_STALE_RETRY_ATTEMPTS: int = 1

    # Model Artifacts Storage
    MODEL_ARTIFACTS_DIR: str | None = None

    # LLM Provider Configuration
    LLM_PROVIDER: str = "mock"  # "mock" | "gemini" | "openai"
    LLM_MODEL_ID: str = ""
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    LLM_TIMEOUT_SECONDS: float = 30.0
    LLM_MAX_RETRIES: int = 3
    LLM_MAX_OUTPUT_TOKENS: int = 4096


settings = Settings()
