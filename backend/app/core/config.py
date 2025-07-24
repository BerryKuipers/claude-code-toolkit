"""
Strongly typed application configuration using Pydantic Settings.

This provides C#-like configuration management with validation and
environment variable support.
"""

import os
from functools import lru_cache
from typing import Optional

from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings with strong typing and validation.
    
    Similar to C# IConfiguration with automatic environment variable binding
    and validation.
    """
    
    # API Configuration
    api_title: str = Field("Crypto Portfolio API", description="API title")
    api_description: str = Field("Strongly typed FastAPI backend for crypto portfolio analysis", description="API description")
    api_version: str = Field("1.0.0", description="API version")
    debug: bool = Field(False, description="Debug mode")
    
    # Server Configuration
    host: str = Field("0.0.0.0", description="Server host")
    port: int = Field(8000, description="Server port")
    reload: bool = Field(True, description="Auto-reload on code changes")
    
    # Bitvavo API Configuration
    bitvavo_api_key: str = Field(..., description="Bitvavo API key")
    bitvavo_api_secret: str = Field(..., description="Bitvavo API secret")
    bitvavo_rate_limit_delay: float = Field(0.2, description="Rate limit delay in seconds")
    
    # AI Configuration
    openai_api_key: Optional[str] = Field(None, description="OpenAI API key")
    anthropic_api_key: Optional[str] = Field(None, description="Anthropic API key")
    default_ai_model: str = Field("claude-sonnet-4", description="Default AI model")
    ai_temperature: float = Field(0.1, description="AI response temperature")
    ai_max_tokens: int = Field(4000, description="Maximum AI response tokens")
    
    # Cache Configuration
    cache_ttl_seconds: int = Field(300, description="Cache TTL in seconds")
    enable_caching: bool = Field(True, description="Enable response caching")
    
    # CORS Configuration
    cors_origins: list = Field(["http://localhost:8501", "http://127.0.0.1:8501"], description="Allowed CORS origins")
    cors_allow_credentials: bool = Field(True, description="Allow CORS credentials")
    cors_allow_methods: list = Field(["*"], description="Allowed CORS methods")
    cors_allow_headers: list = Field(["*"], description="Allowed CORS headers")
    
    # Logging Configuration
    log_level: str = Field("INFO", description="Logging level")
    log_format: str = Field("%(asctime)s - %(name)s - %(levelname)s - %(message)s", description="Log format")
    
    # Database Configuration (for future use)
    database_url: Optional[str] = Field(None, description="Database URL for caching/persistence")
    
    @validator('bitvavo_api_key', 'bitvavo_api_secret')
    def validate_bitvavo_credentials(cls, v):
        if not v:
            raise ValueError('Bitvavo API credentials must be provided')
        # Allow shorter keys for testing
        if len(v) < 5:
            raise ValueError('Bitvavo API credentials must be at least 5 characters')
        return v
    
    @validator('ai_temperature')
    def validate_temperature_range(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('AI temperature must be between 0.0 and 1.0')
        return v
    
    @validator('port')
    def validate_port_range(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError('Port must be between 1 and 65535')
        return v
    
    @validator('log_level')
    def validate_log_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'Log level must be one of: {valid_levels}')
        return v.upper()
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "env_prefix": "",
    }


@lru_cache()
def get_settings() -> Settings:
    """
    Get application settings with caching.
    
    Similar to C# dependency injection for IConfiguration.
    Uses LRU cache to ensure settings are loaded only once.
    
    Returns:
        Settings: Application configuration
    """
    return Settings()
