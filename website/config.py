"""
Configuration for Booklet Website
"""
import os

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'booklet-website-secret-key-change-in-production')
    API_BASE_URL = os.environ.get('API_BASE_URL', 'http://localhost:8000/api/v1')
    ERP_URL = os.environ.get('ERP_URL', 'http://localhost:5000')
    
    # Session
    SESSION_COOKIE_SECURE = False  # Set to True in production
    SESSION_COOKIE_HTTPONLY = True
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SESSION_COOKIE_SECURE = True


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
