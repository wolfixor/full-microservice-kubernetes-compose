"""Redis configuration for comment service."""

from pydantic_settings import BaseSettings


class RedisSettings(BaseSettings):
    """Redis settings for comment service."""
    
    # For Kubernetes: "redis-service", For Docker Compose: "redis"
    REDIS_HOST: str = "redis-service"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""
    REDIS_KEY_PREFIX: str = "comment"
    CACHE_EXPIRE_SECONDS: int = 300  # 5 minutes
    
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


redis_settings = RedisSettings()