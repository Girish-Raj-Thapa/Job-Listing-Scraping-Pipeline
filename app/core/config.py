from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Job Scraper"
    app_env: str = "development"
    debug: bool = True
    log_level: str = "INFO"
    api_port: int = 8001
    scheduled_scrape_interval_hours: int = 6
    beat_poll_interval_minutes: int = 15

    postgres_db: str = "jobs_db"
    postgres_user: str = "jobs_user"
    postgres_password: str = "jobs_password"
    postgres_host: str = "postgres"
    postgres_port: int = 5432

    database_url: str = "postgresql+psycopg://jobs_user:jobs_password@postgres:5432/jobs_db"

    redis_host: str = "redis"
    redis_port: int = 6379
    redis_url: str = "redis://redis:6379/0"

    celery_broker_url: str = "redis://redis:6379/0"
    celery_result_backend: str = "redis://redis:6379/1"

    usajobs_api_key: str | None = None
    usajobs_user_agent: str | None = None
    adzuna_app_id: str | None = None
    adzuna_app_key: str | None = None

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


settings = Settings()
