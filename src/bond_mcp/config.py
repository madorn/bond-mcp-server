"""Configuration management for Bond MCP Server."""

import os
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class BondConfig(BaseSettings):
    """Bond MCP Server configuration."""
    
    # Bond Bridge settings
    bond_token: str = Field(description="Bond API token")
    bond_host: str = Field(description="Bond Bridge IP address or hostname")
    
    # Connection settings
    timeout: float = Field(default=10.0, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum number of API retries")
    retry_delay: float = Field(default=1.0, description="Delay between retries in seconds")
    
    # Logging settings
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log message format"
    )
    
    # MCP settings
    server_name: str = Field(default="bond-mcp-server", description="MCP server name")
    server_version: str = Field(default="0.1.0", description="MCP server version")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    @field_validator('bond_host')
    @classmethod
    def validate_host(cls, v):
        """Validate Bond host format."""
        if not v:
            raise ValueError("Bond host cannot be empty")
        # Remove protocol if present
        if v.startswith(('http://', 'https://')):
            v = v.split('://', 1)[1]
        # Remove trailing slash
        return v.rstrip('/')
    
    @field_validator('bond_token')
    @classmethod
    def validate_token(cls, v):
        """Validate Bond token format."""
        if not v:
            raise ValueError("Bond token cannot be empty")
        if len(v) < 10:
            raise ValueError("Bond token appears to be too short")
        return v
    
    @field_validator('timeout')
    @classmethod
    def validate_timeout(cls, v):
        """Validate timeout value."""
        if v <= 0:
            raise ValueError("Timeout must be positive")
        return v
    
    @field_validator('max_retries')
    @classmethod
    def validate_max_retries(cls, v):
        """Validate max retries value."""
        if v < 0:
            raise ValueError("Max retries cannot be negative")
        return v
    
    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {', '.join(valid_levels)}")
        return v.upper()


def get_config() -> BondConfig:
    """Get Bond configuration from environment variables and .env file."""
    return BondConfig()


def validate_config(config: Optional[BondConfig] = None) -> BondConfig:
    """Validate configuration and return validated config.
    
    Args:
        config: Optional config instance to validate
        
    Returns:
        Validated configuration
        
    Raises:
        ValueError: If configuration is invalid
    """
    if config is None:
        config = get_config()
    
    # Additional validation can be added here
    # For example, checking if Bond bridge is reachable
    
    return config