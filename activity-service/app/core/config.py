"""Configuration management for activity service."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    APP_NAME: str = "activity-service"
    APP_VERSION: str = "1.0.0"

    POSTGRES_HOST: str = "activity-service-db"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "activity_db"
    POSTGRES_USER: str = ""
    POSTGRES_PASSWORD: str = ""

    ROOT_PATH: str = ""

    KAFKA_ENABLED: bool = True
    KAFKA_BOOTSTRAP_SERVERS: str = "platform-kafka-kafka-bootstrap.kafka.svc:9092"
    KAFKA_CONSUMER_GROUP_ID: str = "activity-service"
    KAFKA_AUTO_OFFSET_RESET: str = "earliest"

    HOST: str = "0.0.0.0"
    PORT: int = 8000

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
