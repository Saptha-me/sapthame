"""
Configuration management for the Saptha orchestrator.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseConfig(BaseModel):
    """Database configuration."""
    url: str = Field(description="PostgreSQL connection URL")
    echo: bool = Field(default=False, description="Enable SQL query logging")
    pool_size: int = Field(default=10, description="Connection pool size")
    max_overflow: int = Field(default=20, description="Max overflow connections")


class OrchestratorConfig(BaseModel):
    """Orchestrator configuration."""
    max_concurrent_agents: int = Field(default=5, description="Maximum concurrent agents")
    default_timeout: float = Field(default=30.0, description="Default timeout for agent calls")
    health_check_interval: int = Field(default=60, description="Health check interval in seconds")
    retry_attempts: int = Field(default=3, description="Number of retry attempts for failed requests")
    retry_delay: float = Field(default=1.0, description="Base delay between retries")


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: str = Field(default="INFO", description="Log level")
    format: str = Field(default="json", description="Log format (json or text)")
    include_timestamp: bool = Field(default=True, description="Include timestamp in logs")
    include_caller: bool = Field(default=False, description="Include caller info in logs")


class AgentConfig(BaseModel):
    """Individual agent configuration."""
    id: str
    name: str
    description: str
    capabilities: List[str]
    endpoint: str
    timeout: Optional[float] = None
    retry_attempts: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SapthaConfig(BaseSettings):
    """Main configuration for Saptha orchestrator."""
    
    model_config = SettingsConfigDict(
        env_prefix="SAPTHA_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # Database settings
    database: DatabaseConfig = Field(
        default_factory=lambda: DatabaseConfig(
            url="postgresql+asyncpg://saptha:saptha@localhost:5432/saptha"
        )
    )
    
    # Orchestrator settings
    orchestrator: OrchestratorConfig = Field(default_factory=OrchestratorConfig)
    
    # Logging settings
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    
    # Agent configurations
    agents: List[AgentConfig] = Field(default_factory=list)
    
    # Environment
    environment: str = Field(default="development", description="Environment (development, staging, production)")
    debug: bool = Field(default=False, description="Enable debug mode")
    
    @classmethod
    def from_file(cls, config_file: str) -> SapthaConfig:
        """Load configuration from a file."""
        import json
        import yaml
        
        if config_file.endswith('.json'):
            with open(config_file, 'r') as f:
                data = json.load(f)
        elif config_file.endswith(('.yml', '.yaml')):
            with open(config_file, 'r') as f:
                data = yaml.safe_load(f)
        else:
            raise ValueError("Config file must be JSON or YAML")
        
        return cls(**data)
    
    def get_database_url(self) -> str:
        """Get the database URL, with environment variable override."""
        return os.getenv("DATABASE_URL", self.database.url)
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"
    
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"


# Global configuration instance
_config: Optional[SapthaConfig] = None


def get_config() -> SapthaConfig:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = SapthaConfig()
    return _config


def set_config(config: SapthaConfig) -> None:
    """Set the global configuration instance."""
    global _config
    _config = config


def load_config(config_file: Optional[str] = None) -> SapthaConfig:
    """Load configuration from file or environment."""
    if config_file:
        config = SapthaConfig.from_file(config_file)
    else:
        config = SapthaConfig()
    
    set_config(config)
    return config
