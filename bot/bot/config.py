from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    bot_token: str
    api_url: str = "http://api:8000"
    proxy_url: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()