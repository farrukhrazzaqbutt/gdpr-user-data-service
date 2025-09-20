from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://app:app@localhost:5432/app"
    redis_url: str = "redis://localhost:6379/0"
    
    # Security
    secret_key: str = "your-secret-key-here-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Encryption
    master_key: str = "your-master-encryption-key-here-32-bytes"
    encryption_algorithm: str = "AES-GCM"
    
    # App
    debug: bool = True
    environment: str = "development"
    
    class Config:
        env_file = ".env"


settings = Settings()
