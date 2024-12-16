from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "FastAPI Template"

    # Security
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # MongoDB
    MONGODB_URL: str
    MONGODB_DB_NAME: str

    # Google OAuth
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: Optional[str] = None

    # AWS Configuration
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "ap-south-1"

    # Logging
    LOG_LEVEL: str = "INFO"
    CLOUDWATCH_LOG_GROUP: Optional[str] = None
    CLOUDWATCH_LOG_STREAM: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()