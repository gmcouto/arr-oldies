---
phase: 03-media-inventory-history-timestamp-correlator
plan: 02
subsystem: inventory
tags:
  - history-indexing
  - correlation
  - legacy-fallback
  - inventory-engine
  - filtering
  - sorting
  - multi-instance
requires:
  - 03-01
provides:
  - HistoryCorrelator
  - RadarrHistoryIndex
  - SonarrHistoryIndex
  - InventoryEngine
affects:
  - 04-interactive-terminal-ui-and-cli-reporting
  - 05-safe-mutation-engine-and-action-execution
tech_stack:
  - Python 3.11+
  - Pydantic v2
  - Pytest
key_files:
  - src/arr_oldies/inventory/correlator.py
  - src/arr_oldies/inventory/engine.py
  - src/arr_oldies/inventory/__init__.py
  - tests/test_correlator_radarr.py
  - tests/test_correlator_sonarr.py
  - tests/test_correlator_legacy.py
  - tests/test_inventory_engine.py
  - tests/test_inventory_integration.py
decisions:
  - Multi-key dictionary hash indices (fileId, importedPath, downloadId, movieId/seriesId) index 100k+ events in $O(N+M)$ linear time.
  - HistoryCorrelator resolves grabbed events via exact downloadId first, preventing cross-release date skew on upgraded files.
  - Legacy files with missing or pruned history cleanly fallback to date_added, tagged with is_legacy=True, has_history=False, and history_status=HistoryStatus.LEGACY.
  - InventoryEngine provides single-pass multi-predicate filtering and deterministic tie-breaking for sorting.
metrics:
  new_tests: 19
  total_tests: 149
  test_pass_rate: 100%
  completed_date: "2026-08-24"
---

# Plan 03-02 Summary: History Timestamp Correlator & Inventory Processing Engine

## Executive Summary

Plan 03-02 implemented the core correlation and inventory processing layer for Arr-Oldies:
1. High-performance, $O(N+M)$ in-memory hash indexing and History API event correlation for Radarr and Sonarr instances (`HistoryCorrelator`, `RadarrHistoryIndex`, `SonarrHistoryIndex`).
2. Resilient fallback for legacy and untracked media files whose history records have been purged or pruned, accurately tagging them without failing scan execution.
3. Multi-episode badge formatting (`S01E01-E02`) and multi-audio language extraction.
4. The composable `InventoryEngine` providing single-pass multi-predicate filtering (language, instance, size, age, date cutoffs, legacy/history flags), deterministic sorting with stable tie-breaking, and aggregate summary metric calculation.
5. Multi-instance end-to-end integration tests verifying complete pipeline execution across mixed Radarr and Sonarr collections.

---

## Tasks Completed

### Task 1: History Event Indexing, Radarr/Sonarr Correlation Engine & Legacy Fallback (Tracer)
- Implemented `RadarrHistoryIndex` and `SonarrHistoryIndex` in `src/arr_oldies/inventory/correlator.py` indexing import and grab events by file ID, path, download ID, movie ID, series ID, and episode ID in $O(N+M)$ time.
- Implemented `HistoryCorrelator` mapping `InstanceMediaData` into unified `MediaInventoryItem` records:
  - Exact correlation of `downloadFolderImported`/`movieFileImported`/`episodeFileImported` events.
  - Exact grab event matching via `downloadId` or movie/episode IDs before import timestamp.
  - Clean fallback for legacy items with missing history to `file.date_added` with `is_legacy=True`, `has_history=False`, and `history_status=HistoryStatus.LEGACY`.
  - Sonarr multi-episode badge formatting (`S01E01-E02`).
  - Audio language normalization and extraction.
- Created `tests/test_correlator_radarr.py`, `tests/test_correlator_sonarr.py`, and `tests/test_correlator_legacy.py`.
- Commit: `ba1cdb7 feat(03-02): history indexing, radarr/sonarr correlation engine and legacy fallback`

### Task 2: Inventory Processing Engine with Composable Filtering, Deterministic Sorting & Summary Metrics
- Implemented `InventoryEngine` in `src/arr_oldies/inventory/engine.py`:
  - `filter_inventory`: composable evaluation of media types, instance names, size bounds (bytes), age bounds (days), before/after date cutoffs, legacy/history flags, and audio languages using `LanguageNormalizer.matches()`.
  - `sort_inventory`: deterministic sorting for `import_date`, `grab_date`, `size`, `title`, and `age` with stable tie-breaking.
  - `generate_summary`: computes total items, total size, movie/episode/legacy counts, oldest/newest timestamps, and per-instance distribution.
- Updated `src/arr_oldies/inventory/__init__.py` re-exporting `HistoryCorrelator`, `RadarrHistoryIndex`, `SonarrHistoryIndex`, and `InventoryEngine`.
- Created `tests/test_inventory_engine.py`.
- Commit: `588a07a feat(03-02): inventory filtering, deterministic sorting and summary metrics engine`

### Task 3: End-to-End Multi-Instance Inventory Pipeline Integration Verification
- Created `tests/test_inventory_integration.py` assembling a 4-instance scenario (`radarr-4k`, `radarr-hd` legacy, `sonarr-anime` multi-episode dual-audio, and `sonarr-tv`).
- Verified full pipeline execution: ingestion -> correlation -> legacy tagging -> multi-predicate filtering -> deterministic sorting -> summary metric generation.
- Verified 100% test pass rate across all 149 test cases in the test suite.
- Commit: `5cddf7e test(03-02): end-to-end multi-instance inventory pipeline integration tests`

---

## Threat Mitigations

| Threat ID | Mitigation |
|---|---|
| **T-03-03** (Denial of Service / Quadratic Search) | Implemented `RadarrHistoryIndex` and `SonarrHistoryIndex` hash tables (`fileId`, `importedPath`, `downloadId`, `movieId`, `seriesId`, `episodeId`) providing $O(1)$ lookups per file and $O(N+M)$ total processing time. |
| **T-03-04** (Information Integrity / Release Skew) | `HistoryCorrelator` correlates grab events via exact `downloadId` match first, ensuring upgraded files are matched to their specific download release rather than prior release iterations. |
| **T-03-05** (Crash on Pruned History) | `HistoryCorrelator` detects empty or missing history events and seamlessly falls back to `file.date_added`, setting `is_legacy=True`, `has_history=False`, and `history_status=HistoryStatus.LEGACY` without throwing exceptions [INVT-06]. |

---

## Verification Summary

- **Pytest Suite:** 149 passed in 0.95s (100% green)
- **Unit Tests:**
  - `tests/test_correlator_radarr.py` (4 passed)
  - `tests/test_correlator_sonarr.py` (3 passed)
  - `tests/test_correlator_legacy.py` (2 passed)
  - `tests/test_inventory_engine.py` (9 passed)
  - `tests/test_inventory_integration.py` (1 passed)
- **All Previous Phase 01, 02, and 03-01 Tests:** Passed cleanly with zero regressions.
