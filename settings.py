from typing import Optional
try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
    USE_MODEL_CONFIG = True
except ImportError:
    from pydantic import BaseSettings
    USE_MODEL_CONFIG = False


class Settings(BaseSettings):
    database_url: Optional[str] = None
    openai_api_key: Optional[str] = None
    supabase_url: Optional[str] = None
    supabase_anon_key: Optional[str] = None
    debug: bool = False
    guest_session_ttl_hours: int = 24

    if USE_MODEL_CONFIG:
        model_config = SettingsConfigDict(env_file=".env", extra="ignore", env_file_encoding="utf-8")
    else:
        class Config:
            env_file = ".env"
            extra = "ignore"
            env_file_encoding = "utf-8"


settings = Settings()

