from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    allowed_origins: str = Field(default="*", alias="ALLOWED_ORIGINS")
    alert_dns_entropy_threshold: float = Field(
        default=4.0, alias="ALERT_DNS_ENTROPY_THRESHOLD"
    )
    alert_connection_threshold: int = Field(
        default=120, alias="ALERT_CONNECTION_THRESHOLD"
    )


settings = Settings()
