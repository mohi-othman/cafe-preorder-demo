from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")

    database_url: str = "postgresql+psycopg://qahwati:qahwati@localhost:5432/cafe"
    web_origin: str = "http://localhost:3000"
    jwt_secret: str = ""  # required for logins
    admin_password: str = ""  # used by the seed only
    barista_password: str = ""  # used by the seed only


settings = Settings()
