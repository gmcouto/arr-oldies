---
phase: 07-scope-unmonitor-to-episodes-and-add-unmonitor-series-option
status: passed
verified: 2026-08-24T10:13:20Z
verifier: gsd-verifier
requirements_verified:
  - ACT-03
  - ACT-04
must_haves_verified:
  - "ActionType enum includes UNMONITOR and UNMONITOR_SERIES, and removes UNMONITOR_EPISODE [ACT-03, ACT-04]"
  - "ActionExecutor unmonitors specific episodes for TV items and movies for movie items under ActionType.UNMONITOR [ACT-03, ACT-04]"
  - "ActionExecutor unmonitors parent series for TV items under ActionType.UNMONITOR_SERIES with series deduplication [ACT-03]"
  - "CLI clean command removes --unmonitor-episode and adds --unmonitor-series option [ACT-03, ACT-04]"
  - "CLI clean --unmonitor triggers episode unmonitoring for Sonarr items and movie unmonitoring for Radarr items [ACT-03, ACT-04]"
  - "CLI clean --unmonitor-series triggers series unmonitoring in Sonarr [ACT-03]"
automated_checks_passed: 236
coverage: 100%
---

# Phase 07: Scope unmonitor to episodes and add unmonitor-series option — Verification Report

## Phase Goal Verification

**Goal:** Ensure `--unmonitor` operates on individual media items (episodes for TV files, movies for movie files), remove `--unmonitor-episode`, and add `--unmonitor-series` for full series unmonitoring.

### 1. Requirements Traceability

| Requirement ID | Requirement Summary | Status | Proof / Evidence |
|---|---|---|---|
| **ACT-03** | Support unmonitoring movies in Radarr and parent series in Sonarr via `--unmonitor-series` | **VERIFIED** | `tests/test_action_executor.py::test_execute_plan_unmonitor_series`, `tests/test_cli_clean.py::test_cli_clean_unmonitor_series_action` |
| **ACT-04** | Support granular episode unmonitoring via `--unmonitor` on TV items | **VERIFIED** | `tests/test_action_executor.py::test_execute_plan_deletions_and_unmonitoring`, `tests/test_cli_clean.py::test_cli_clean_unmonitor_actions` |

### 2. Must-Haves Verification

- **Action Domain Models (`src/arr_oldies/actions/models.py`)**:
  - `ActionType` defines `UNMONITOR = "unmonitor"` and `UNMONITOR_SERIES = "unmonitor_series"`.
  - `UNMONITOR_EPISODE` is completely removed.
- **Action Execution Engine (`src/arr_oldies/actions/executor.py`)**:
  - `ActionType.UNMONITOR` executes item-level unmonitoring: `/api/v3/movie/editor` for movies and `/api/v3/episode/monitor` for episode items.
  - `ActionType.UNMONITOR_SERIES` executes `/api/v3/series/editor` with per-series deduplication.
  - `build_plan` prunes `UNMONITOR_SERIES` on movie items.
- **CLI Options (`src/arr_oldies/cli.py`)**:
  - `clean` command provides `--unmonitor` and `--unmonitor-series` flags.
  - Removed `--unmonitor-episode` flag.
- **Automated Tests**:
  - All 236 unit and integration tests pass cleanly.
  - Linters and mypy type checks pass with 0 errors.
