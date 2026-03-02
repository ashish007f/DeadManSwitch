"""
Application configuration.

Loads from environment variables with sensible defaults.
"""

from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Union


class Settings(BaseSettings):
    """Application settings from environment"""
    
    # Project Metadata
    app_name: str = "I'mGood"
    app_description: str = "Local-first check-in system for daily safety"
    app_version: str = "0.1.0"
    
    # CORS
    allowed_origins: Union[str, List[str]] = ["*"]

    @field_validator("allowed_origins", mode="after")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    # Check-in interval in minutes (for scheduler)
    check_interval_minutes: int = 1
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Rate Limiting
    rate_limit_auth: str = "3/hour"
    rate_limit_general: str = "5/hour"
    
    # Security
    # !!! GENERATE A NEW STRONG SECRET FOR PRODUCTION !!!
    secret_key: str = "dev-secret-key-placeholder" # OVERRIDE IN PROD
    phone_salt: str = "dev-phone-salt-placeholder" # OVERRIDE IN PROD
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30

    # Email notifications to trusted contacts
    resend_api_key: str = "test_api_key" # OVERRIDE IN PROD
    resend_sender: str = "I'mGood <onboarding@resend.dev>"
    
    # Paths
    frontend_dist: str = "" # Set via ENV in production
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
