from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


ENV_PATH = Path(__file__).resolve().parent.parent.parent / "infra" / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_PATH,
        case_sensitive=False,
        extra="ignore",
    )

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

    # Cloud.ru (Whisper)
    cloud_ru_api_key: str = ""
    cloud_ru_base_url: str = ""
    whisper_model: str = ""

    # Selectel (LLM)
    selectel_api_key: str = ""
    selectel_base_url: str = "https://api.tf.selcloud.ru/v1"
    selectel_llm_model: str = "qwen3.8-27b"


settings = Settings()