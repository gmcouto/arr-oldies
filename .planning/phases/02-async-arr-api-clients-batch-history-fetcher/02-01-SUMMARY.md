---
phase: 02-async-arr-api-clients-batch-history-fetcher
plan: 01
subsystem: api
tags:
  - httpx
  - pydantic
  - rest-api
  - retry-backoff
  - sqlite-locks
requires:
  - 01-config-targeting-connectivity-probe
provides:
  - src/arr_oldies/api/models.py
  - src/arr_oldies/api/base.py
  - src/arr_oldies/exceptions.py
  - src/arr_oldies/constants.py
affects:
  - 02-02
tech-stack:
  added: []
  patterns:
    - Pydantic v2 schemas with `extra="ignore"` and `populate_by_name=True` for forward compatibility
    - Connection pooling limits (`max_connections=10`, `max_keepalive_connections=5`) via HTTPX
    - Exponential backoff with random jitter and `Retry-After` header support
    - SQLite database lock error detection and automated retries
    - Masked credentials via `SecretStr.get_secret_value()` injected strictly in headers
key-files:
  created:
    - src/arr_oldies/api/__init__.py
    - src/arr_oldies/api/models.py
    - src/arr_oldies/api/base.py
    - tests/test_api_models.py
    - tests/test_base_client.py
  modified:
    - src/arr_oldies/constants.py
    - src/arr_oldies/exceptions.py
key-decisions:
  - "Configured ApiBaseModel with `extra='ignore'` to ensure forward compatibility across minor *arr API versions"
  - "Implemented SQLite lock pattern matching for status 500/503 responses containing 'database is locked', 'sqlitebusyexception', or 'sqlite error 5'"
  - "Enforced connection limits (10 max connections, 5 keepalive) to prevent socket contention on low-resource home servers"
requirements-completed:
  - API-01
  - API-02
  - API-03
  - API-04
duration: 2 min
completed: 2026-08-23T23:40:20Z
coverage:
  - deliverable: "Pydantic v2 API data models for Radarr and Sonarr REST API schemas"
    verification:
      kind: automated
      ref: tests/test_api_models.py
      status: pass
    human_judgment: false
  - deliverable: "BaseArrClient HTTPX async engine with connection pooling and credential protection"
    verification:
      kind: automated
      ref: tests/test_base_client.py#test_base_client_headers_and_config
      status: pass
    human_judgment: false
  - deliverable: "Exponential backoff with jitter and Retry-After header parsing"
    verification:
      kind: automated
      ref: tests/test_base_client.py#test_base_client_retry_on_429_with_retry_after
      status: pass
    human_judgment: false
  - deliverable: "SQLite database lock detection and retry mitigation"
    verification:
      kind: automated
      ref: tests/test_base_client.py#test_base_client_sqlite_lock_detection_and_retry
      status: pass
    human_judgment: false
  - deliverable: "Domain exception mapping for 401/403/404/timeouts/connection errors"
    verification:
      kind: automated
      ref: tests/test_base_client.py
      status: pass
    human_judgment: false
---

# Phase 02 Plan 01: API Models & BaseArrClient Infrastructure Summary

Established foundational Pydantic v2 data models, API client exception hierarchy, and `BaseArrClient` HTTPX async engine with connection pooling, exponential backoff with jitter, SQLite lock detection, and credential protection.

## Accomplishments

1. **Pydantic v2 API Schemas (`src/arr_oldies/api/models.py`)**:
   - Implemented `MediaInfo` model for audio/video stream parameters (codecs, channels, audio languages, resolution, etc.).
   - Created typed Radarr models: `RadarrMovie`, `RadarrMovieFile`, `RadarrHistoryRecord`, `RadarrHistoryPage`.
   - Created typed Sonarr models: `SonarrSeries`, `SonarrSeason`, `SonarrEpisodeFile`, `SonarrEpisode`, `SonarrHistoryRecord`, `SonarrHistoryPage`.
   - Configured all models with `ConfigDict(extra="ignore", populate_by_name=True)` for forward compatibility.

2. **Domain Exception Taxonomy (`src/arr_oldies/exceptions.py`)**:
   - Added `ArrClientError` as base exception.
   - Added `ArrConnectionError`, `ArrTimeoutError`, `ArrAuthenticationError`, `ArrNotFoundError`, `ArrResponseError`, and `ArrDatabaseLockedError`.

3. **BaseArrClient Async Engine (`src/arr_oldies/api/base.py`)**:
   - Managed connection pool limits (`10` max connections, `5` keepalive connections, `30.0s` keepalive expiry).
   - Injected `X-Api-Key` safely from `SecretStr` along with `User-Agent` and `Accept` headers.
   - Built retry loop with exponential backoff and random jitter for transient errors (429, 502, 503, 504).
   - Added SQLite lock detection for 500/503 responses indicating database lock conditions.
   - Provided typed HTTP convenience methods (`get`, `post`, `put`, `delete`).

4. **Comprehensive Test Suites (`tests/test_api_models.py`, `tests/test_base_client.py`)**:
   - 15 unit tests covering deserialization, field aliases, extra field tolerance, retries, lock detection, timeout mapping, and auth error handling.

## Deviations from Plan

None - plan executed exactly as written.

## Verification

```bash
.venv/bin/pytest tests/test_api_models.py tests/test_base_client.py -v
```
All 15 tests passed.

## Self-Check: PASSED
- `src/arr_oldies/api/models.py` exists: YES
- `src/arr_oldies/api/base.py` exists: YES
- `tests/test_api_models.py` exists: YES
- `tests/test_base_client.py` exists: YES
- Commits `fd760ef` and `ee96576` recorded: YES
- Test suite passes 100%: YES
