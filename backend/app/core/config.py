"""
Strongly typed application configuration using Pydantic Settings.

This provides C#-like configuration management with validation and
environment variable support.
"""

from functools import lru_cache
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings with strong typing and validation.

    Similar to C# IConfiguration with automatic environment variable binding
    and validation.
    """

    def __hash__(self):
        """Make Settings hashable for LRU cache."""
        return hash(
            (
                self.api_title,
                self.api_version,
                self.bitvavo_api_key,
                self.bitvavo_api_secret,
                self.debug,
            )
        )

    # API Configuration
    api_title: str = Field("Crypto Portfolio API", description="API title")
    api_description: str = Field(
        "Strongly typed FastAPI backend for crypto portfolio analysis",
        description="API description",
    )
    api_version: str = Field("1.0.0", description="API version")
    debug: bool = Field(False, description="Debug mode")

    # Server Configuration
    host: str = Field("localhost", description="Server host")
    port: int = Field(8000, description="Server port")
    reload: bool = Field(True, description="Auto-reload on code changes")

    # Bitvavo API Configuration
    bitvavo_api_key: str = Field(..., description="Bitvavo API key")
    bitvavo_api_secret: str = Field(..., description="Bitvavo API secret")
    bitvavo_rate_limit_delay: float = Field(
        0.2, description="Rate limit delay in seconds"
    )

    # Clean Architecture Configuration
    use_clean_architecture: bool = Field(
        default=True, description="Use Clean Architecture implementation"
    )
    portfolio_cache_ttl: int = Field(
        default=300, description="Portfolio data cache TTL in seconds"
    )

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
    cors_origins: list = Field(
        ["http://localhost:8501", "http://127.0.0.1:8501"],
        description="Allowed CORS origins",
    )
    cors_allow_credentials: bool = Field(True, description="Allow CORS credentials")
    cors_allow_methods: list = Field(["*"], description="Allowed CORS methods")
    cors_allow_headers: list = Field(["*"], description="Allowed CORS headers")

    # Logging Configuration
    log_level: str = Field("INFO", description="Logging level")
    log_format: str = Field(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s", description="Log format"
    )

    # Database Configuration (for future use)
    database_url: Optional[str] = Field(
        None, description="Database URL for caching/persistence"
    )

    # Development Cache Configuration
    enable_dev_cache: bool = Field(
        True, description="Enable local SQLite cache for development"
    )
    dev_cache_path: str = Field(
        "data/dev_cache.db", description="Path to development cache database"
    )
    cache_portfolio_ttl_hours: int = Field(
        1, description="Portfolio data cache TTL in hours"
    )
    cache_prices_ttl_minutes: int = Field(
        5, description="Price data cache TTL in minutes"
    )
    cache_trades_ttl_hours: int = Field(
        24, description="Trade history cache TTL in hours"
    )
    cache_deposits_ttl_hours: int = Field(
        24, description="Deposit history cache TTL in hours"
    )
    cache_withdrawals_ttl_hours: int = Field(
        24, description="Withdrawal history cache TTL in hours"
    )

    @field_validator("bitvavo_api_key", "bitvavo_api_secret")
    @classmethod
    def validate_bitvavo_credentials(cls, v):
        if not v:
            raise ValueError("Bitvavo API credentials must be provided")
        # Allow shorter keys for testing
        if len(v) < 5:
            raise ValueError("Bitvavo API credentials must be at least 5 characters")
        return v

    @field_validator("ai_temperature")
    @classmethod
    def validate_temperature_range(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError("AI temperature must be between 0.0 and 1.0")
        return v

    @field_validator("port")
    @classmethod
    def validate_port_range(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()

    model_config = {
        "env_file": [".env", "../.env", "../../.env"],
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "env_prefix": "",
        "extra": "ignore",  # Allow extra fields in environment
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
