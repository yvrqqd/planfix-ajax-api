from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ServiceConfig(BaseSettings):
    swagger_enabled: bool = Field(default=False, alias="SWAGGER_ENABLED")
    headless: bool = Field(default=True, alias="BROWSER_HEADLESS")
    timeout: float = Field(default=30000.0, alias="BROWSER_TIMEOUT")

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")


SERVICE_CONFIG = ServiceConfig()
