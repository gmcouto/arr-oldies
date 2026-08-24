"""Pydantic v2 data models for configuration, instances, and probing results."""

from enum import StrEnum
from pydantic import BaseModel, Field, SecretStr, field_validator, model_validator


class InstanceType(StrEnum):
    """Supported *arr service instance types."""

    RADARR = "radarr"
    SONARR = "sonarr"


class DefaultsConfig(BaseModel):
    """Global default settings applied to all instances unless explicitly overridden."""

    timeout: float = Field(default=30.0, ge=1.0, le=300.0)
    verify_ssl: bool = Field(default=True)


class InstanceConfig(BaseModel):
    """Configuration for an individual Radarr or Sonarr instance."""

    name: str = Field(..., min_length=1, max_length=64)
    type: InstanceType
    url: str = Field(...)
    api_key: SecretStr = Field(...)
    timeout: float | None = Field(default=None, ge=1.0, le=300.0)
    verify_ssl: bool | None = Field(default=None)

    @field_validator("url")
    @classmethod
    def sanitize_url(cls, v: str) -> str:
        """Strip trailing slashes and ensure valid HTTP/HTTPS protocol."""
        url_clean = str(v).strip().rstrip("/")
        if not (url_clean.startswith("http://") or url_clean.startswith("https://")):
            raise ValueError("URL must start with http:// or https://")
        return url_clean


class AppConfig(BaseModel):
    """Root application configuration schema."""

    defaults: DefaultsConfig = Field(default_factory=DefaultsConfig)
    instances: list[InstanceConfig] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_and_merge_instances(self) -> "AppConfig":
        """Validate unique instance names and inherit defaults for unset fields."""
        seen_names: set[str] = set()
        for inst in self.instances:
            norm_name = inst.name.lower()
            if norm_name in seen_names:
                raise ValueError(f"Duplicate instance name found: '{inst.name}'")
            seen_names.add(norm_name)

            if inst.timeout is None:
                inst.timeout = self.defaults.timeout
            if inst.verify_ssl is None:
                inst.verify_ssl = self.defaults.verify_ssl

        return self


class ProbeResult(BaseModel):
    """Result of an individual instance health and connectivity probe."""

    instance_name: str
    instance_type: InstanceType
    url: str
    success: bool
    version: str | None = None
    latency_ms: float = 0.0
    error_message: str | None = None
