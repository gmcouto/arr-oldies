# Phase 7: Scope unmonitor to episodes and add unmonitor-series option - Research

## User Constraints & Requirements

- `--unmonitor` flag when targeting TV episodes should unmonitor individual episodes via `/api/v3/episode/monitor`, not the whole series. For movies in Radarr, `--unmonitor` continues to unmonitor the movie via `/api/v3/movie/editor`.
- Remove `--unmonitor-episode` option completely from the CLI and domain model.
- Add `--unmonitor-series` option to allow users to explicitly unmonitor the entire parent series in Sonarr via `/api/v3/series/editor`.
- All dry-run simulations, confirmation panels, JSON outputs, and execution reports must accurately reflect the new action types and semantics.
- All unit and integration test suites must be updated and pass cleanly.

---

## Component Analysis & Affected Files

1. **`src/arr_oldies/actions/models.py`**:
   - Update `ActionType` enum:
     - `UNMONITOR = "unmonitor"`
     - `UNMONITOR_SERIES = "unmonitor_series"`
     - Remove `UNMONITOR_EPISODE`
2. **`src/arr_oldies/actions/executor.py`**:
   - `build_plan`:
     - Prune `UNMONITOR_SERIES` on `MediaType.MOVIE` items.
   - `execute_plan`:
     - `ActionType.UNMONITOR`:
       - Radarr -> `client.unmonitor_movie(item.movie_id)`
       - Sonarr -> `client.unmonitor_episodes(item.episode_ids)`
     - `ActionType.UNMONITOR_SERIES`:
       - Sonarr -> `client.unmonitor_series(item.series_id)` with deduplication across episodes in the same series.
3. **`src/arr_oldies/actions/confirmation.py`**:
   - Update action styling, labels, and impact summaries to format `UNMONITOR` as item-level unmonitoring and `UNMONITOR_SERIES` as series-level unmonitoring.
4. **`src/arr_oldies/cli.py`**:
   - Remove `--unmonitor-episode` option from `clean` command.
   - Add `--unmonitor-series` option to `clean` command.
   - Update help text for `--unmonitor` to clarify item-level scoping (movies in Radarr, episodes in Sonarr).
5. **Tests**:
   - `tests/test_action_models.py`: Update `ActionType` enum tests.
   - `tests/test_action_executor.py`: Update tests for unmonitor scoping and series unmonitoring.
   - `tests/test_cli_clean.py`: Update CLI options tests, replacing `--unmonitor-episode` with `--unmonitor-series` and testing `--unmonitor` on episode items.

---

## Validation Architecture

- **Unit tests**:
  - `tests/test_action_models.py`
  - `tests/test_action_executor.py`
  - `tests/test_sonarr_client_actions.py`
  - `tests/test_radarr_client_actions.py`
- **CLI integration tests**:
  - `tests/test_cli_clean.py`
- **Full suite**:
  - `pytest -v`
  - `ruff check .`
  - `mypy src/`
