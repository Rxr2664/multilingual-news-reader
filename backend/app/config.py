from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://news:news@localhost:5432/news"
    sync_database_url: str = "postgresql://news:news@localhost:5432/news"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret: str = "dev-secret"
    jwt_algorithm: str = "HS256"
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/auth/google/callback"
    frontend_url: str = "http://localhost:3000"
    demo_login_enabled: bool = True
    worker_poll_seconds: int = 900
    lemma_cache_ttl: int = 60 * 60 * 24 * 30
    score_cache_ttl: int = 60 * 60 * 24
    bulk_invalidation_threshold: int = 50


settings = Settings()
