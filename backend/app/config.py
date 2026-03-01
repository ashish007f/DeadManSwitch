"""
Application configuration.

Loads from environment variables with sensible defaults.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings from environment"""
    
    # Database
    database_url: str = "sqlite:///./checkin.db"
    
    # Check-in interval in minutes (for scheduler)
    check_interval_minutes: int = 1
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Security
    secret_key: str = "dev-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30

    # Email notifications to trusted contacts
    resend_api_key: str = "test_api_key"
    resend_sender: str = "I'mGood <onboarding@resend.dev>"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
