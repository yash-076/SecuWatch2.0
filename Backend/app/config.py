from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    redis_url: str
    device_cache_ttl_seconds: int = 600
    heartbeat_online_threshold_seconds: int = 90
    auto_create_database: bool = True
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int
    refresh_token_expire_days: int
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_client_id: str = "secuwatch-backend"
    kafka_logs_topic: str = "logs"
    kafka_alerts_topic: str = "alerts"
    kafka_heartbeat_topic: str = "heartbeat"
    kafka_replication_factor: int = 1
    kafka_producer_retries: int = 3
    kafka_producer_request_timeout_ms: int = 5000
    kafka_consumer_group_prefix: str = "secuwatch"
    gemini_api_key: str | None = None
    llm_api_key: str | None = None
    llm_api_url: str = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
    llm_model: str = "gemini-2.0-flash"
    llm_timeout_seconds: int = 30
    ai_cache_ttl_seconds: int = 600
    alert_dedupe_window_seconds: int = 300
    app_log_level: str = "DEBUG"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()  # type: ignore[call-arg]
