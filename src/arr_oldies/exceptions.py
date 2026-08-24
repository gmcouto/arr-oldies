"""Exception hierarchy for arr-oldies domain errors."""


class ArrOldiesError(Exception):
    """Base domain exception for all arr-oldies errors."""


class ConfigError(ArrOldiesError):
    """Base exception for configuration-related errors (exit code 2)."""


class ConfigNotFoundError(ConfigError):
    """Raised when the specified or discovered configuration file cannot be found."""


class ConfigFormatError(ConfigError):
    """Raised when the configuration file contains invalid YAML syntax."""


class ConfigValidationError(ConfigError):
    """Raised when configuration values fail Pydantic schema validation."""


class InstanceError(ArrOldiesError):
    """Base exception for instance-targeting and resolution errors (exit code 2)."""


class InstanceNotFoundError(InstanceError):
    """Raised when a requested instance name is not found in the configuration."""


class InstanceConflictError(InstanceError):
    """Raised when conflicting targeting flags or filters are supplied."""


class ProbeError(ArrOldiesError):
    """Base exception for health check probing failures (exit code 1)."""
