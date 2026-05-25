from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""
    log_level: str = "INFO"
    mcp_host: str = "127.0.0.1"
    mcp_port: int = 8765
    api_host: str = "127.0.0.1"
    api_port: int = 8000


settings = Settings()
