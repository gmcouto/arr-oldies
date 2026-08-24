---
phase: 08-support-monitored-and-unmonitored-filter-for-scan-and-clean
status: passed
verified: 2026-08-24T11:15:30Z
verifier: gsd-verifier
requirements_verified:
  - INVT-03
  - ACT-02
must_haves_verified:
  - "MediaInventoryItem captures monitored boolean status from Radarr movies and Sonarr episodes/series [INVT-03]"
  - "InventoryFilter supports monitored_only and unmonitored_only filtering [INVT-03]"
  - "InventoryEngine filters items accurately when monitored_only or unmonitored_only criteria are set [INVT-03]"
  - "CLI scan and clean expose --monitored (with aliases --monitored-only, --only-monitored) and --unmonitored (with aliases --unmonitored-only, --only-unmonitored) [INVT-03, ACT-02]"
  - "CLI scan and clean validate mutual exclusion and exit with code 2 and message 'Cannot specify both --monitored and --unmonitored filter flags.' when both are passed [INVT-03, ACT-02]"
  - "CLI clean --unmonitor --only-monitored isolates and unmonitors only monitored media items [ACT-02]"
  - "JSON export includes monitored boolean field on each serialized inventory item [INVT-03]"
automated_checks_passed: 246
coverage: 100%
---

# Phase 08: Support --monitored and --unmonitored filter for scan and clean — Verification Report

## Phase Goal Verification

**Goal:** Enable filtering media items by monitored status across Radarr movies and Sonarr episodes in `scan` and `clean` commands (e.g., `--only-monitored` / `--monitored-only` and `--unmonitored-only`).

### 1. Requirements Traceability

| Requirement ID | Requirement Summary | Status | Proof / Evidence |
|---|---|---|---|
| **INVT-03** | Build unified media item inventory records capturing monitored boolean metadata, and filter by monitored status in `InventoryFilter` / `InventoryEngine` / `scan` | **VERIFIED** | `tests/test_inventory_models.py::test_media_inventory_item_monitored_field`, `tests/test_correlator_radarr.py::test_correlate_radarr_monitored_status`, `tests/test_correlator_sonarr.py::test_correlate_sonarr_monitored_status_single_and_multi_episode`, `tests/test_inventory_engine.py::test_filter_by_monitored_flags`, `tests/test_cli_scan.py::test_cli_scan_monitored_filters` |
| **ACT-02** | Target actions and clean simulations with monitored/unmonitored filters (e.g. `clean --unmonitor --only-monitored`) | **VERIFIED** | `tests/test_cli_clean.py::test_cli_clean_monitored_and_unmonitored_filters` |

### 2. Must-Haves Verification

- **Inventory Models (`src/arr_oldies/inventory/models.py`)**:
  - `MediaInventoryItem` includes `monitored: bool = True` with backwards-compatible default.
  - `InventoryFilter` includes `monitored_only: bool = False` and `unmonitored_only: bool = False`.
  - JSON serialization preserves `"monitored": true` / `"monitored": false`.
- **History Correlator (`src/arr_oldies/inventory/correlator.py`)**:
  - `_correlate_radarr` extracts `movie.monitored` (fallback `True` when movie is missing).
  - `_correlate_sonarr` extracts `any(ep.monitored for ep in episodes)` for multi-episode files, falling back to `series.monitored` (fallback `True`).
- **Inventory Engine (`src/arr_oldies/inventory/engine.py`)**:
  - `filter_inventory` evaluates `criteria.monitored_only` and `criteria.unmonitored_only` correctly during inventory filtering.
- **CLI Commands (`src/arr_oldies/cli.py`)**:
  - `scan` and `clean` expose `--monitored` (aliases `--monitored-only`, `--only-monitored`) and `--unmonitored` (aliases `--unmonitored-only`, `--only-unmonitored`).
  - Strict mutual exclusion validation prints `"Cannot specify both --monitored and --unmonitored filter flags."` and exits with code 2 (`EXIT_CONFIG_ERROR`).
- **Automated Tests**:
  - 61 unit and integration tests covering the monitored filtering subsystem passed.
  - Full automated suite: 246/246 tests passed in 4.89s.
  - Linters and static type checker: `ruff check .` and `mypy src/` passed with 0 errors.
