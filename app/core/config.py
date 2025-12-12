"""
Application Configuration Module
Handles all environment variables and application settings.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """
    # MongoDB Configuration
    mongodb_url: str = "mongodb://localhost:27017"
    master_db_name: str = "master_database"
    
    # JWT Configuration
    secret_key: str = "your-super-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Application Configuration
    debug: bool = True
    app_name: str = "Organization Management Service"
    app_version: str = "1.0.0"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """
    Returns cached settings instance.
    Using lru_cache ensures settings are only loaded once.
    """
    return Settings()


settings = get_settings()
