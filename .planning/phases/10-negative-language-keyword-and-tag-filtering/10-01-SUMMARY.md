---
phase: 10-negative-language-keyword-and-tag-filtering
plan: "01"
subsystem: api
tags: [radarr, sonarr, tags, inventory, history]

# Dependency graph
requires:
  - phase: 04-inventory-engine
    provides: MediaInventoryItem, HistoryCorrelator, MultiInstanceFetcher
provides:
  - Tag model and /api/v3/tag endpoint support in Radarr and Sonarr clients
  - Resilient tag retrieval in MultiInstanceFetcher with error fallback
  - Resolved tag labels on MediaInventoryItem via HistoryCorrelator dynamic mapping
affects: [10-02, inventory-filtering, cli]

# Actuals
actuals:
  tokens: 14000
  tasks: 2
  commits: 1

# Tech tracking
tech-stack:
  added: []
  patterns: [per-instance tag ID to label resolution map]

key-files:
  created: []
  modified:
    - src/arr_oldies/constants.py
    - src/arr_oldies/api/models.py
    - src/arr_oldies/api/radarr.py
    - src/arr_oldies/api/sonarr.py
    - src/arr_oldies/api/fetcher.py
    - src/arr_oldies/inventory/models.py
    - src/arr_oldies/inventory/correlator.py
    - tests/test_api_models.py
    - tests/test_radarr_client.py
    - tests/test_sonarr_client.py
    - tests/test_history_fetcher.py
    - tests/test_inventory_models.py
    - tests/test_correlator_radarr.py
    - tests/test_correlator_sonarr.py

key-decisions:
  - "Resilient tag fetching gracefully defaults to empty list on 500 or network failure rather than failing the scan"
  - "HistoryCorrelator resolves integer tag IDs into string label lists per instance to avoid ID collision across instances"

patterns-established:
  - "Per-instance tags_by_id dictionary lookup in HistoryCorrelator"

requirements-completed:
  - INVT-09

coverage:
  - id: D1
    description: "Tag model deserializes id and label from /api/v3/tag endpoint responses"
    requirement: "INVT-09"
    verification:
      - kind: unit
        ref: "tests/test_api_models.py#test_tag_model_parsing"
        status: pass
    human_judgment: false
  - id: D2
    description: "RadarrMovie and SonarrSeries parse tags lists of integer tag IDs"
    requirement: "INVT-09"
    verification:
      - kind: unit
        ref: "tests/test_api_models.py#test_radarr_movie_and_sonarr_series_tags_parsing"
        status: pass
    human_judgment: false
  - id: D3
    description: "RadarrClient and SonarrClient fetch tag definitions via get_tags()"
    requirement: "INVT-09"
    verification:
      - kind: unit
        ref: "tests/test_radarr_client.py#test_radarr_get_tags"
        status: pass
      - kind: unit
        ref: "tests/test_sonarr_client.py#test_sonarr_get_tags"
        status: pass
    human_judgment: false
  - id: D4
    description: "MultiInstanceFetcher retrieves tags concurrently with resilience fallback to empty list on error"
    requirement: "INVT-09"
    verification:
      - kind: unit
        ref: "tests/test_history_fetcher.py#test_fetch_instance_data_with_tags_and_fallback"
        status: pass
    human_judgment: false
  - id: D5
    description: "MediaInventoryItem captures resolved string tag labels rather than raw integer IDs"
    requirement: "INVT-09"
    verification:
      - kind: unit
        ref: "tests/test_inventory_models.py#test_media_inventory_item_tags_field"
        status: pass
    human_judgment: false
  - id: D6
    description: "HistoryCorrelator maps movie and series numeric tag IDs to human-readable tag labels"
    requirement: "INVT-09"
    verification:
      - kind: unit
        ref: "tests/test_correlator_radarr.py#test_correlate_radarr_movie_tag_label_mapping"
        status: pass
      - kind: unit
        ref: "tests/test_correlator_sonarr.py#test_correlate_sonarr_series_tag_label_mapping"
        status: pass
    human_judgment: false

# Metrics
duration: 4min
completed: 2026-08-24
status: complete
---

# Phase 10: Plan 01 Summary

**Tag API schemas, client endpoints, resilient multi-instance fetcher, and dynamic tag label resolution in HistoryCorrelator**

## Performance

- **Duration:** 4 min
- **Started:** 2026-08-24T19:41:45Z
- **Completed:** 2026-08-24T19:44:00Z
- **Tasks:** 2
- **Files modified:** 14

## Accomplishments
- Added `RADARR_TAG_ENDPOINT` and `SONARR_TAG_ENDPOINT` in `constants.py`
- Defined `Tag` model and added `tags` lists of integer IDs to `RadarrMovie` and `SonarrSeries`
- Added async `get_tags()` methods to `RadarrClient` and `SonarrClient`
- Extended `MultiInstanceFetcher` to fetch instance tags concurrently and resiliently with fallback
- Added `tags: list[str]` to `MediaInventoryItem`
- Implemented instance-scoped tag ID-to-label resolution in `HistoryCorrelator._correlate_radarr` and `_correlate_sonarr`
- Added comprehensive unit test coverage for models, clients, fetchers, and correlators

## Task Commits

1. **Task 1 & 2: Tag models, endpoints, fetcher, and correlator resolution** - `d5fb9a6` (feat)

## Files Created/Modified
- `src/arr_oldies/constants.py` - Added `/api/v3/tag` endpoint constants
- `src/arr_oldies/api/models.py` - Added Tag schema and tags integer ID fields on movies and series
- `src/arr_oldies/api/radarr.py` - Added get_tags() method
- `src/arr_oldies/api/sonarr.py` - Added get_tags() method
- `src/arr_oldies/api/fetcher.py` - Added tags field and resilient fetcher integration
- `src/arr_oldies/inventory/models.py` - Added tags list[str] to MediaInventoryItem
- `src/arr_oldies/inventory/correlator.py` - Added dynamic tag ID-to-label mapping in correlation methods
- `tests/test_api_models.py` - Unit tests for Tag and tags deserialization
- `tests/test_radarr_client.py` - Unit tests for RadarrClient.get_tags()
- `tests/test_sonarr_client.py` - Unit tests for SonarrClient.get_tags()
- `tests/test_history_fetcher.py` - Unit tests for tag fetching and fallback
- `tests/test_inventory_models.py` - Unit tests for MediaInventoryItem.tags
- `tests/test_correlator_radarr.py` - Unit tests for Radarr tag label mapping
- `tests/test_correlator_sonarr.py` - Unit tests for Sonarr tag label mapping

## Decisions Made
- Resilient tag fetching gracefully defaults to empty list on HTTP errors or exceptions so that failing tag endpoints never abort full inventory scans.
- Dynamic tag label resolution is performed per-instance inside `HistoryCorrelator` using instance-specific `tags_by_id` dictionaries to prevent tag ID collisions across different Radarr/Sonarr servers.

## Deviations from Plan
None - plan executed exactly as written.

## Issues Encountered
None.

## Next Phase Readiness
- Tag retrieval and resolved labels on `MediaInventoryItem` are ready for downstream filter predicates in Plan 10-02 (InventoryFilter, InventoryEngine, and CLI).

---
*Phase: 10-negative-language-keyword-and-tag-filtering*
*Completed: 2026-08-24*
