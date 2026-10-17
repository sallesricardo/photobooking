from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://photobooking:photobooking@localhost:5432/photobooking"
    frontend_origin: str = "http://localhost:3000"
    app_timezone: str = "America/Sao_Paulo"
    calendar_provider: str = "mock"
    app_secret_key: str = "change-me-in-production"
    whatsapp_phone: str = "5511999999999"

    # Admin authentication (demo/portfolio). Use strong secrets in production.
    admin_username: str = "admin"
    admin_password: str = "change-me-admin"
    admin_session_minutes: int = 60
    admin_cookie_secure: bool = False

    rate_limit_enabled: bool = True
    rate_limit_requests: int = 60
    rate_limit_window_seconds: int = 60

    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/v1/google/callback"
    google_calendar_id: str = "primary"
    google_token_path: str = "/app/data/google_token.json"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
