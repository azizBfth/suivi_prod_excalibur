"""
Configuration settings for the FastAPI application.
"""

import os
from functools import lru_cache
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""
    
    # Application settings
    app_name: str = "Suivi Production - Excalibur ERP"
    app_description: str = "API pour le suivi en temps réel des indicateurs de production"
    app_version: str = "2.0.0"
    debug: bool = False
    
    # Database settings
    db_uid: Optional[str] = None
    db_pwd: Optional[str] = None
    db_host: Optional[str] = None
    db_server_name: Optional[str] = None
    db_database_name: Optional[str] = None
    
    # Server settings
    host: str = "localhost"
    port: int = 80
    reload: bool = True

    # Logging settings
    log_level: str = "info"

    # Email/SMTP settings
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    from_email: Optional[str] = None
    alert_email_recipients: Optional[str] = None

    # Alert settings
    enable_alerts: bool = True
    alert_check_interval: int = 60*60*12  # seconds (12 hours)

    # Monitoring settings
    enable_performance_monitoring: bool = True
    slow_query_threshold: float = 2.0  # seconds

    # Authentication settings
    jwt_secret_key: str = "your-secret-key-change-this-in-production-make-it-long-and-random"
    access_token_expire_minutes: int = 480  # 8 hours

    # Default admin credentials (change in production)
    default_admin_username: str = "admin"
    default_admin_password: str = "admin123"
    default_user_username: str = "user"
    default_user_password: str = "user123"
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
