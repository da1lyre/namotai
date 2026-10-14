from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    app_env: str = "dev"

    # Database
    database_url: str

    # Media
    media_dir: str = "/data/media"
    max_file_size_mb: int = 100
    max_video_duration_sec: int = 7200

    # Rate limit
    rate_limit_per_day: int = 5

    # Cloud.ru
    cloud_ru_api_key: str
    cloud_ru_base_url: str
    whisper_model: str
    llm_model: str

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()