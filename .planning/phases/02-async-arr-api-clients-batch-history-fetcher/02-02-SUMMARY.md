---
phase: 02-async-arr-api-clients-batch-history-fetcher
plan: 02
subsystem: api
tags:
  - radarr
  - sonarr
  - pagination
  - multi-instance
  - error-isolation
  - async-concurrency
requires:
  - 02-01
provides:
  - src/arr_oldies/api/radarr.py
  - src/arr_oldies/api/sonarr.py
  - src/arr_oldies/api/factory.py
  - src/arr_oldies/api/fetcher.py
affects:
  - 03-media-inventory-history-correlation-engine
tech-stack:
  added: []
  patterns:
    - Typed endpoint querying for Radarr and Sonarr v3/v4 APIs
    - Semaphore-throttled fetching for sub-resource requests (`asyncio.Semaphore(3)`)
    - Sequential batch history pagination with termination conditions
    - Multi-instance concurrent orchestration via `asyncio.gather` with isolated error boundaries
key-files:
  created:
    - src/arr_oldies/api/radarr.py
    - src/arr_oldies/api/sonarr.py
    - src/arr_oldies/api/factory.py
    - src/arr_oldies/api/fetcher.py
    - tests/test_radarr_client.py
    - tests/test_sonarr_client.py
    - tests/test_history_fetcher.py
  modified:
    - src/arr_oldies/api/__init__.py
key-decisions:
  - "Implemented RadarrClient with full library (`/api/v3/movie`), moviefile (`/api/v3/moviefile`), and history (`/api/v3/history`, `/api/v3/history/movie`) endpoints"
  - "Implemented SonarrClient with series (`/api/v3/series`), episode files (`/api/v3/episodefile`), episodes (`/api/v3/episode`), and history (`/api/v3/history`, `/api/v3/history/series`) endpoints"
  - "Throttled multi-series episode file fetching with asyncio.Semaphore(3) to prevent socket and database contention"
  - "Orchestrated multi-instance scans concurrently in MultiInstanceFetcher using isolated error boundaries so failing instances record diagnostic warnings without aborting healthy instances"
requirements-completed:
  - API-01
  - API-02
  - API-03
  - API-04
duration: 3 min
completed: 2026-08-23T23:42:20Z
coverage:
  - deliverable: "RadarrClient endpoint queries and batch history pagination"
    verification:
      kind: automated
      ref: tests/test_radarr_client.py
      status: pass
    human_judgment: false
  - deliverable: "SonarrClient endpoint queries and throttled episode file fetching"
    verification:
      kind: automated
      ref: tests/test_sonarr_client.py
      status: pass
    human_judgment: false
  - deliverable: "Client factory instantiating typed RadarrClient and SonarrClient"
    verification:
      kind: automated
      ref: tests/test_history_fetcher.py#test_create_client_factory
      status: pass
    human_judgment: false
  - deliverable: "MultiInstanceFetcher concurrent multi-instance scanning with complete error isolation"
    verification:
      kind: automated
      ref: tests/test_history_fetcher.py#test_fetch_all_instances_data_concurrency_and_error_isolation
      status: pass
    human_judgment: false
---

# Phase 02 Plan 02: RadarrClient, SonarrClient & MultiInstanceFetcher Summary

Implemented typed async clients for Radarr and Sonarr REST API v3/v4 endpoints, sequential batch history pagination engines, throttled episode file fetching, client instantiation factory, and the resilient `MultiInstanceFetcher` for concurrent multi-instance data acquisition with isolated error boundaries.

## Accomplishments

1. **Radarr REST API Client (`src/arr_oldies/api/radarr.py`)**:
   - Implemented `get_movies()`, `get_movie()`, `get_movie_files()`, `get_history()`, and `get_movie_history()`.
   - Built `iter_history()` async generator and `fetch_all_history()` batch aggregator with progress callbacks.

2. **Sonarr REST API Client (`src/arr_oldies/api/sonarr.py`)**:
   - Implemented `get_series()`, `get_series_by_id()`, `get_episode_files()`, `get_all_episode_files()`, `get_episodes()`, `get_history()`, and `get_series_history()`.
   - Added concurrency throttling (`asyncio.Semaphore(DEFAULT_SERIES_CONCURRENCY)`) when fetching episode files across multiple series.
   - Built `iter_history()` and `fetch_all_history()` batch history retrieval.

3. **Client Factory & MultiInstanceFetcher (`src/arr_oldies/api/factory.py`, `src/arr_oldies/api/fetcher.py`)**:
   - Added `create_client()` factory mapping `InstanceType` to `RadarrClient` or `SonarrClient`.
   - Built `MultiInstanceFetcher` coordinating concurrent library and history acquisition across multiple instances with `asyncio.gather`.
   - Isolated instance failures (401 unauthorized, connection errors, timeouts) into structured `InstanceFetchResult` diagnostic records without aborting healthy instances.

4. **Integration Test Suites (`tests/test_radarr_client.py`, `tests/test_sonarr_client.py`, `tests/test_history_fetcher.py`)**:
   - 16 new unit/integration tests verifying endpoint response parsing, history pagination termination, throttling, factory resolution, and error isolation.

## Deviations from Plan

None - plan executed exactly as written.

## Verification

```bash
.venv/bin/pytest tests/test_radarr_client.py tests/test_sonarr_client.py tests/test_history_fetcher.py -v
```
All 16 tests passed.

## Self-Check: PASSED
- `src/arr_oldies/api/radarr.py` exists: YES
- `src/arr_oldies/api/sonarr.py` exists: YES
- `src/arr_oldies/api/factory.py` exists: YES
- `src/arr_oldies/api/fetcher.py` exists: YES
- `tests/test_radarr_client.py` exists: YES
- `tests/test_sonarr_client.py` exists: YES
- `tests/test_history_fetcher.py` exists: YES
- Commits `93e61ac`, `ae68d39`, `3af05d5` recorded: YES
- Test suite passes 100%: YES
