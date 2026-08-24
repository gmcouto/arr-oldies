---
quick_id: 260824-fwt
slug: add-option-unmonitor-season-for-unmonito
description: add option --unmonitor-season for unmonitoring the whole season
status: complete
date: 2026-08-24
---

# Quick Task Summary: Add option --unmonitor-season for unmonitoring the whole season

## Work Done
1. **Action Domain Models**:
   - Added `UNMONITOR_SEASON = "unmonitor_season"` to `ActionType` enum in `src/arr_oldies/actions/models.py`.
2. **Sonarr Client**:
   - Implemented `SonarrClient.unmonitor_season(series_id: int, season_number: int) -> bool` in `src/arr_oldies/api/sonarr.py` to retrieve the series object, update the matching season's `monitored` flag to `False`, and `PUT` the modified series back to `/api/v3/series/{id}`.
3. **Action Execution Engine**:
   - Updated `ActionExecutor.build_plan()` to prune `UNMONITOR_SEASON` (and `UNMONITOR_SERIES`) for movie items.
   - Updated `ActionExecutor.execute_plan()` to execute `unmonitor_season` against Sonarr with in-memory deduplication across multiple episodes in the same season via `unmonitored_seasons` set tracking `(instance_name, series_id, season_number)`.
4. **CLI Command**:
   - Added `--unmonitor-season` option to Typer CLI `clean` command in `src/arr_oldies/cli.py`.
   - Updated action validation error message to list `--delete, --unmonitor, --unmonitor-season, --unmonitor-series, --remove`.
5. **Documentation & Tests**:
   - Synchronized `README.md` features, command documentation, and usage examples.
   - Added comprehensive unit and integration tests across `tests/test_action_models.py`, `tests/test_sonarr_client_actions.py`, `tests/test_action_executor.py`, and `tests/test_cli_clean.py`.
