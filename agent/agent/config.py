from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AgentSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    server_url: str = Field(default="http://127.0.0.1:8000", alias="SERVER_URL")
    interval_seconds: int = Field(default=30, alias="AGENT_INTERVAL_SECONDS")
    agent_version: str = Field(default="0.1.0", alias="AGENT_VERSION")


settings = AgentSettings()
