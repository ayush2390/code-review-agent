from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    LLM_API_KEY: str
    GITHUB_API_URL: str = "https://api.github.com"

    
    class Config:
        env_file = ".env"  # Specifies the environment file

settings = Settings()
