"""
Application configuration.

Loads from environment variables with sensible defaults.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings from environment"""
    
    # Project Metadata
    app_name: str = "I'mGood"
    app_description: str = "Local-first check-in system for daily safety"
    app_version: str = "0.1.0"
    
    # Database
    database_url: str = "sqlite:///./checkin.db"
    
    # Check-in interval in minutes (for scheduler)
    check_interval_minutes: int = 1
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Rate Limiting
    rate_limit_auth: str = "5/minute"
    rate_limit_general: str = "10/minute"
    
    # Security
    secret_key: str = "dev-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30

    # Email notifications to trusted contacts
    resend_api_key: str = "test_api_key"
    resend_sender: str = "I'mGood <onboarding@resend.dev>"
    
    # Paths
    frontend_dist: str = "" # Set via ENV in production
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
