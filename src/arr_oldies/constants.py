"""Constants and default configuration parameters for arr-oldies."""

# Process exit codes (per D-14)
EXIT_SUCCESS: int = 0
EXIT_PROBE_ERROR: int = 1
EXIT_CONFIG_ERROR: int = 2

# Configuration file discovery defaults (per D-01)
CONFIG_FILENAMES: list[str] = [
    "arr-oldies.yaml",
    "arr-oldies.yml",
    "config.yaml",
    "config.yml",
]

# Network and HTTP defaults
DEFAULT_TIMEOUT: float = 30.0
DEFAULT_CONNECT_TIMEOUT: float = 5.0
DEFAULT_USER_AGENT: str = "arr-oldies/0.1.0"
API_KEY_HEADER: str = "X-Api-Key"

# *arr API endpoints (per D-05)
API_STATUS_ENDPOINT: str = "/api/v3/system/status"
