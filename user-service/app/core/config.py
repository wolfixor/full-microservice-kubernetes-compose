"""Configuration management for user service."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    APP_NAME: str = "user-service"
    APP_VERSION: str = "1.0.0"
    
    # Database (read from environment variables)
    POSTGRES_HOST: str = "user-service-db"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "user_db"
    POSTGRES_USER: str = ""
    POSTGRES_PASSWORD: str = ""
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8001
    
    @property
    def DATABASE_URL_SYNC(self) -> str:
        """Generate synchronous database URL."""
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    @property
    def DATABASE_URL_ASYNC(self) -> str:
        """Generate asynchronous database URL."""
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()