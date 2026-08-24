---
phase: 08-support-monitored-and-unmonitored-filter-for-scan-and-clean
plan: 01
subsystem: inventory
tags:
  - inventory
  - filtering
  - monitored
  - unmonitored
  - cli
  - scan
  - clean
requires:
  - 03-01
  - 03-02
  - 04-01
  - 05-01
provides:
  - Monitored status extraction for Radarr movies and Sonarr TV episodes/series
  - Monitored / unmonitored filtering in InventoryFilter and InventoryEngine
  - CLI --monitored and --unmonitored filter flags with aliases and mutual exclusion validation
  - Targeted actions in clean command filtered by monitored status (e.g. clean --unmonitor --only-monitored)
affects:
  - src/arr_oldies/inventory/models.py
  - src/arr_oldies/inventory/correlator.py
  - src/arr_oldies/inventory/engine.py
  - src/arr_oldies/cli.py
  - tests/test_inventory_models.py
  - tests/test_correlator_radarr.py
  - tests/test_correlator_sonarr.py
  - tests/test_inventory_engine.py
  - tests/test_cli_scan.py
  - tests/test_cli_clean.py
tech_stack:
  - python
  - typer
  - pydantic-v2
  - httpx
  - pytest
  - respx
key_decisions:
  - "Added monitored boolean field with default True to MediaInventoryItem and monitored_only / unmonitored_only flags to InventoryFilter."
  - "Correlators resolve monitored status from Radarr movie.monitored (fallback True) and Sonarr episodes with any(ep.monitored) fallback to series.monitored (fallback True)."
  - "Added CLI flags --monitored (aliases: --monitored-only, --only-monitored) and --unmonitored (aliases: --unmonitored-only, --only-unmonitored) to both scan and clean commands."
  - "Enforced mutual exclusion between --monitored and --unmonitored in CLI scan and clean commands with exit code 2 and explicit error message."
requirements_completed:
  - INVT-03
  - ACT-02
duration_minutes: 5
completed_date: "2026-08-24"
---

# Phase 08 Plan 01: Support --monitored and --unmonitored Filter for Scan and Clean Summary

## Executive Summary
Implemented monitored status extraction, filtering, and CLI integration across `scan` and `clean` commands. `MediaInventoryItem` now captures `monitored: bool` from Radarr movies and Sonarr episodes/series. `InventoryFilter` and `InventoryEngine` support `monitored_only` and `unmonitored_only` evaluation. CLI `scan` and `clean` commands expose `--monitored` (with aliases `--monitored-only`, `--only-monitored`) and `--unmonitored` (with aliases `--unmonitored-only`, `--only-unmonitored`) with strict mutual exclusion validation.

## Tasks Completed

| Task ID | Description | Commits |
|---|---|---|
| `08-01-01` | Add monitored status to `MediaInventoryItem`, `InventoryFilter`, correlators, and `InventoryEngine`, with unit tests | `dddc7cf` (`feat(08-01): add monitored status to models, correlators, and inventory engine`) |
| `08-01-02` | Add CLI options, mutual exclusion validation, and clean/scan integration tests | `341ae61` (`feat(08-01): add --monitored and --unmonitored filters to CLI scan and clean`) |

## Verification Results

- Unit tests in `tests/test_inventory_models.py`, `tests/test_correlator_radarr.py`, `tests/test_correlator_sonarr.py`, and `tests/test_inventory_engine.py` passed cleanly (31/31).
- CLI integration tests in `tests/test_cli_scan.py` and `tests/test_cli_clean.py` passed cleanly (30/30).
- Full automated test suite: 246/246 passed in 5.81s.
- Linters & static type checker: `ruff check .` and `mypy src/` passed with 0 errors.

## Artifacts Created / Modified

- `src/arr_oldies/inventory/models.py`: Added `monitored: bool = True` to `MediaInventoryItem` and `monitored_only`, `unmonitored_only` to `InventoryFilter`.
- `src/arr_oldies/inventory/correlator.py`: Propagated monitored status from Radarr movies and Sonarr episodes/series.
- `src/arr_oldies/inventory/engine.py`: Added monitored filtering rules in `filter_inventory`.
- `src/arr_oldies/cli.py`: Added `--monitored` / `--unmonitored` options and mutual exclusion checks to `scan` and `clean`.
- `tests/test_inventory_models.py`: Added unit tests for monitored field defaults and serialization.
- `tests/test_correlator_radarr.py`: Added unit tests for Radarr monitored status extraction and fallback.
- `tests/test_correlator_sonarr.py`: Added unit tests for Sonarr single, multi-episode, and series monitored status extraction.
- `tests/test_inventory_engine.py`: Added unit tests for `monitored_only` and `unmonitored_only` filtering.
- `tests/test_cli_scan.py`: Added integration tests for scan monitored/unmonitored filters, aliases, JSON output, and mutual exclusion.
- `tests/test_cli_clean.py`: Added integration tests for clean monitored/unmonitored dry-run, execution, and mutual exclusion.
