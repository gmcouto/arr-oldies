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

# Connection pool limits (per API-03, T-02-02)
DEFAULT_MAX_CONNECTIONS: int = 10
DEFAULT_KEEPALIVE_CONNECTIONS: int = 5
DEFAULT_KEEPALIVE_EXPIRY: float = 30.0

# Retry & backoff constants (per API-03)
DEFAULT_RETRY_ATTEMPTS: int = 3
DEFAULT_BACKOFF_FACTOR: float = 0.5
DEFAULT_MAX_BACKOFF: float = 15.0

# History pagination constants (per API-03, C-04)
DEFAULT_HISTORY_PAGE_SIZE: int = 1000
MIN_HISTORY_PAGE_SIZE: int = 100
MAX_HISTORY_PAGE_SIZE: int = 1000

# Concurrency limits (per API-03, T-02-02)
DEFAULT_SERIES_CONCURRENCY: int = 3

# *arr API endpoints (per D-05, API-01, API-02)
API_STATUS_ENDPOINT: str = "/api/v3/system/status"

# Radarr endpoints (API-01)
RADARR_MOVIE_ENDPOINT: str = "/api/v3/movie"
RADARR_MOVIEFILE_ENDPOINT: str = "/api/v3/moviefile"
RADARR_HISTORY_ENDPOINT: str = "/api/v3/history"
RADARR_HISTORY_MOVIE_ENDPOINT: str = "/api/v3/history/movie"
RADARR_TAG_ENDPOINT: str = "/api/v3/tag"

# Sonarr endpoints (API-02)
SONARR_SERIES_ENDPOINT: str = "/api/v3/series"
SONARR_EPISODEFILE_ENDPOINT: str = "/api/v3/episodefile"
SONARR_EPISODE_ENDPOINT: str = "/api/v3/episode"
SONARR_HISTORY_ENDPOINT: str = "/api/v3/history"
SONARR_HISTORY_SERIES_ENDPOINT: str = "/api/v3/history/series"
SONARR_TAG_ENDPOINT: str = "/api/v3/tag"

# Inventory defaults (per INVT-04, INVT-05)
DEFAULT_SORT_KEY: str = "import_date"
DEFAULT_SORT_DIRECTION: str = "asc"
