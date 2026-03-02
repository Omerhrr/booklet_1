"""
Application Configuration
"""
from pydantic_settings import BaseSettings
from typing import List, Optional
import os
import secrets
import warnings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "ERP Backend API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False  # Default to False for security
    ENVIRONMENT: str = "development"  # development, staging, production
    
    # Database
    DATABASE_URL: str = "sqlite:///./erp.db"
    
    # Security
    SECRET_KEY: str = "your-super-secret-key-change-in-production-min-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_LOGIN_ATTEMPTS: int = 5  # Max login attempts per window
    RATE_LIMIT_LOGIN_WINDOW_MINUTES: int = 15  # Window in minutes
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:5000,http://127.0.0.1:5000"
    
    # Session Security
    SESSION_COOKIE_SECURE: bool = False  # Set True in production with HTTPS
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "lax"
    
    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    @property
    def database_url(self) -> str:
        """Get properly formatted database URL"""
        url = self.DATABASE_URL
        # Fix common URL format issues
        if url.startswith("file:"):
            # Convert file: URL to SQLite URL
            path = url[5:]  # Remove 'file:' prefix
            return f"sqlite:///{path}"
        return url
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.ENVIRONMENT.lower() == "production"
    
    def validate_security_settings(self):
        """Validate security settings and warn about insecure defaults"""
        # Check for default secret key
        default_keys = [
            "your-super-secret-key-change-in-production-min-32-chars",
            "dev-secret-key-change-in-production",
            "secret-key",
            "change-me",
        ]
        
        if self.SECRET_KEY in default_keys:
            if self.is_production:
                raise ValueError(
                    "CRITICAL: Default SECRET_KEY detected in production! "
                    "Set the SECRET_KEY environment variable to a secure random value."
                )
            else:
                warnings.warn(
                    "WARNING: Using default SECRET_KEY. "
                    "Set SECRET_KEY environment variable for production.",
                    UserWarning
                )
        
        # Check minimum secret key length
        if len(self.SECRET_KEY) < 32:
            if self.is_production:
                raise ValueError(
                    "CRITICAL: SECRET_KEY is too short for production! "
                    "Use at least 32 characters."
                )
            else:
                warnings.warn(
                    "WARNING: SECRET_KEY should be at least 32 characters.",
                    UserWarning
                )
        
        # Check DEBUG mode in production
        if self.is_production and self.DEBUG:
            raise ValueError(
                "CRITICAL: DEBUG mode is enabled in production! "
                "Set DEBUG=False for production environment."
            )
        
        # Check for HTTPS in production
        if self.is_production and not self.SESSION_COOKIE_SECURE:
            warnings.warn(
                "WARNING: SESSION_COOKIE_SECURE is False in production. "
                "Cookies should be secure when using HTTPS.",
                UserWarning
            )
        
        return True
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

# Validate security settings on import (but don't crash in development)
try:
    settings.validate_security_settings()
except ValueError as e:
    if settings.is_production:
        raise
    else:
        warnings.warn(str(e), UserWarning)
