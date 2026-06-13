"""Configuration management for task service."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    APP_NAME: str = "task-service"
    APP_VERSION: str = "1.0.0"
    
    # Database
    # POSTGRES_HOST: str = "task-service-db"
    # POSTGRES_PORT: int = 5432
    # POSTGRES_DB: str = "taskdb"
    # POSTGRES_USER: str = "postgres"
    # POSTGRES_PASSWORD: str = "postgres"
    
    # # Server
    # HOST: str = "0.0.0.0"
    # PORT: int = 8002
    
    # class Config:
    #     env_file = ".env"
    #     env_file_encoding = "utf-8"
    #     case_sensitive = False


settings = Settings()