"""Configuration management for search service."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    APP_NAME: str = "search-service"
    APP_VERSION: str = "1.0.0"
    
    # Elasticsearch
    ELASTICSEARCH_HOST: str = "elasticsearch"
    ELASTICSEARCH_PORT: int = 9200
    
    # Redis for caching
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 3  # Different DB than other services
    REDIS_PASSWORD: str = ""
    
    # Service endpoints for data ingestion (simulated events)
    TASK_SERVICE_URL: str = "http://task-service:8000"
    COMMENT_SERVICE_URL: str = "http://comment-service:8000"
    
    # Root path for reverse proxy (Kong)
    ROOT_PATH: str = ""

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    @property
    def ELASTICSEARCH_URL(self) -> str:
        """Generate Elasticsearch URL."""
        return f"http://{self.ELASTICSEARCH_HOST}:{self.ELASTICSEARCH_PORT}"
    
    @property
    def REDIS_URL(self) -> str:
        """Generate Redis URL."""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()