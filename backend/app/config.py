from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg2://proctor:proctor@localhost:5432/proctor"
    jwt_secret: str = "dev-only-change-me"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 120
    cors_origins: str = "http://localhost:5173"
    yolo_model: str = "yolov8n.pt"
    yolo_conf: float = 0.45
    violation_cooldown_seconds: int = 10


settings = Settings()
