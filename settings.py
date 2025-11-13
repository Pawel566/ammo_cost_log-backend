from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str | None = None
    openai_api_key: str | None = None
    supabase_url: str | None = None
    supabase_anon_key: str | None = None
    debug: bool = False
    guest_session_ttl_hours: int = 24

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", env_file_encoding="utf-8")


settings = Settings()

