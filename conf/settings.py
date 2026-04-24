from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # app
    APP_NAME: str = "SentiFlow Agent"
    APP_ENV: str = "dev"
    APP_DEBUG: bool = False
    APP_HOST: str = "127.0.0.1"
    APP_PORT: int = 8000
    APP_API_PREFIX: str = "/api/v1"
    APP_DESCRIPTION: str = "SentiFlow service"
    APP_VERSION: str = "0.1.0"
    LOG_LEVEL: str = "INFO"

    # database
    DATABASE_URL: str = Field(..., description="SQLAlchemy async database url")
    DATABASE_ECHO: bool = False
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_POOL_PRE_PING: bool = True

    # mode
    DASHSCOPE_API_KEY: str = ""
    LLM_BASE_URL: str = ""
    LLM_MODEL_NAME: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


settings = Settings()
