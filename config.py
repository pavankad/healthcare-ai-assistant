"""
Database configuration and settings for EMR application
Follows security best practices with environment variable configuration
"""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

@dataclass
class DatabaseConfig:
    """Database configuration with secure defaults"""
    host: str = os.getenv('DB_HOST', 'localhost')
    port: int = int(os.getenv('DB_PORT', '5432'))
    database: str = os.getenv('DB_NAME', 'emr_database')
    username: str = os.getenv('DB_USER', 'emr_user')
    password: str = os.getenv('DB_PASSWORD', 'emr_password')
    pool_size: int = int(os.getenv('DB_POOL_SIZE', '10'))
    max_overflow: int = int(os.getenv('DB_MAX_OVERFLOW', '20'))
    pool_timeout: int = int(os.getenv('DB_POOL_TIMEOUT', '30'))
    pool_recycle: int = int(os.getenv('DB_POOL_RECYCLE', '3600'))
    
    @property
    def connection_string(self) -> str:
        """Generate PostgreSQL connection string"""
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    @property
    def async_connection_string(self) -> str:
        """Generate async PostgreSQL connection string"""
        return f"postgresql+asyncpg://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"

@dataclass
class AppConfig:
    """Application configuration"""
    secret_key: str = os.getenv('SECRET_KEY', 'emr_secret_key_change_in_production')
    debug: bool = os.getenv('DEBUG', 'True').lower() == 'true'
    host: str = os.getenv('APP_HOST', '0.0.0.0')
    port: int = int(os.getenv('APP_PORT', '5000'))
    session_timeout_hours: int = int(os.getenv('SESSION_TIMEOUT_HOURS', '8'))

# Global configuration instances
db_config = DatabaseConfig()
app_config = AppConfig()
