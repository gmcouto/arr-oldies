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


# API client domain exceptions (per API-04, T-02-01)
class ArrClientError(ArrOldiesError):
    """Base exception for all *arr API client communication failures."""


class ArrConnectionError(ArrClientError):
    """Network connection failure, host unreachable, or DNS resolution failure."""


class ArrTimeoutError(ArrClientError):
    """HTTP request or socket connect timeout exceeded."""


class ArrAuthenticationError(ArrClientError):
    """HTTP 401 or 403: Invalid API key or unauthorized access."""


class ArrNotFoundError(ArrClientError):
    """HTTP 404: Endpoint or requested resource not found."""


class ArrResponseError(ArrClientError):
    """Server returned an unexpected HTTP 4xx or 5xx status code."""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        self.message = message
        super().__init__(f"HTTP {status_code}: {message}")


class ArrDatabaseLockedError(ArrResponseError):
    """Server SQLite database is locked (SQLiteBusyException / SQLite Error 5)."""

    def __init__(self, message: str = "Instance database is locked") -> None:
        super().__init__(status_code=500, message=message)
