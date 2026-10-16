from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://photobooking:photobooking@db:5432/photobooking"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
