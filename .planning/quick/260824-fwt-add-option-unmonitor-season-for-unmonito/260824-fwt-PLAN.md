---
phase: quick
plan: 260824-fwt
type: execute
files_modified:
  - src/arr_oldies/actions/models.py
  - src/arr_oldies/api/sonarr.py
  - src/arr_oldies/actions/executor.py
  - src/arr_oldies/cli.py
  - README.md
  - tests/test_action_models.py
  - tests/test_sonarr_client_actions.py
  - tests/test_action_executor.py
  - tests/test_cli_clean.py
---

# Quick Plan: Add option --unmonitor-season for unmonitoring the whole season

## Objective
Add `--unmonitor-season` CLI option to unmonitor the whole season the episode is in within Sonarr, updating the Sonarr client, action models, action executor, CLI interface, and documentation.

## Tasks

### Task 1: Add UNMONITOR_SEASON ActionType and SonarrClient.unmonitor_season
- In `src/arr_oldies/actions/models.py`, add `UNMONITOR_SEASON = "unmonitor_season"` to `ActionType`.
- In `src/arr_oldies/api/sonarr.py`, implement `unmonitor_season(self, series_id: int, season_number: int) -> bool` which fetches the series by ID, sets `monitored = False` on the targeted season object, and `PUT`s the updated series back to Sonarr.
- Add unit tests in `tests/test_action_models.py` and `tests/test_sonarr_client_actions.py`.

### Task 2: Update ActionExecutor, CLI clean command, and README.md
- In `src/arr_oldies/actions/executor.py`:
  - In `build_plan`, ignore `UNMONITOR_SEASON` for `MediaType.MOVIE`.
  - In `execute_plan`, execute `client.unmonitor_season(item.series_id, item.season_number)` for Sonarr items with deduplication by `(item.instance_name, item.series_id, item.season_number)`.
- In `src/arr_oldies/cli.py`:
  - Add `--unmonitor-season` option to `clean` command.
  - Append `ActionType.UNMONITOR_SEASON` when `--unmonitor-season` is supplied.
  - Update missing action error message to include `--unmonitor-season`.
- In `README.md`:
  - Update feature list, clean command description, and options table with `--unmonitor-season`.
- Add tests in `tests/test_action_executor.py` and `tests/test_cli_clean.py`.
