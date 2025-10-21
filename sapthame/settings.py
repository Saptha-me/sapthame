"""Settings configuration for the sapthame package.

This module defines the configuration settings for the application using pydantic models.
"""

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ProjectSettings(BaseSettings):
    """
    Project-level configuration settings.

    Contains general application settings like environment, debug mode,
    and project metadata.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="PROJECT__",
        extra="allow",
    )

    environment: str = Field(default="development", env="ENVIRONMENT")
    name: str = "sapthame"
    version: str = "0.1.0"

    @computed_field
    @property
    def debug(self) -> bool:
        """Compute debug mode based on environment."""
        return self.environment != "production"

    @computed_field
    @property
    def testing(self) -> bool:
        """Compute testing mode based on environment."""
        return self.environment == "testing"


class LoggingSettings(BaseSettings):
    """Logging configuration settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="LOGGING__",
        extra="allow",
    )

    # Log Directory and File
    log_dir: str = "logs"
    log_filename: str = "sapthame.log"

    # Log Rotation and Retention
    log_rotation: str = "10 MB"
    log_retention: str = "1 week"

    # Log Format
    log_format: str = "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {module}:{function}:{line} | {message}"

    # Log Levels
    default_level: str = "INFO"

    # Rich Theme Colors
    theme_info: str = "bold cyan"
    theme_warning: str = "bold yellow"
    theme_error: str = "bold red"
    theme_critical: str = "bold white on red"
    theme_debug: str = "dim blue"
    theme_did: str = "bold green"
    theme_security: str = "bold magenta"
    theme_agent: str = "bold blue"

    # Rich Console Settings
    traceback_width: int = 120
    show_locals: bool = True


class ObservabilitySettings(BaseSettings):
    """Observability and instrumentation configuration settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="OBSERVABILITY__",
        extra="allow",
    )

    # OpenTelemetry Base Packages
    base_packages: list[str] = [
        "opentelemetry-sdk",
        "opentelemetry-exporter-otlp",
    ]


class Settings(BaseSettings):
    """Main settings class that aggregates all configuration components."""

    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_file=".env",
        extra="allow",
    )

    project: ProjectSettings = ProjectSettings()
    logging: LoggingSettings = LoggingSettings()
    observability: ObservabilitySettings = ObservabilitySettings()


app_settings = Settings()