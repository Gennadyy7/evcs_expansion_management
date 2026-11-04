from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        extra='ignore',
        env_file='.env',
        env_file_encoding='utf-8',
    )

    APP_ROOT_PATH: str = ''

    APP_HOST: str
    APP_PORT: int
    APP_RELOAD: bool

    DOCS_ENABLED: bool

    LOG_LEVEL: Literal['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']


settings = Settings()  # type: ignore[call-arg]
