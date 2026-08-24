---
phase: 07-scope-unmonitor-to-episodes-and-add-unmonitor-series-option
plan: 01
subsystem: actions
tags:
  - actions
  - unmonitor
  - sonarr
  - radarr
  - cli
requires:
  - 05-01
  - 05-02
provides:
  - Scoped episode unmonitoring under ActionType.UNMONITOR for Sonarr media items
  - Series unmonitoring under ActionType.UNMONITOR_SERIES with deduplication
  - Removal of --unmonitor-episode and introduction of --unmonitor-series CLI flags
affects:
  - src/arr_oldies/actions/models.py
  - src/arr_oldies/actions/executor.py
  - src/arr_oldies/actions/confirmation.py
  - src/arr_oldies/cli.py
  - tests/test_action_models.py
  - tests/test_action_executor.py
  - tests/test_cli_clean.py
tech_stack:
  - python
  - typer
  - pydantic-v2
  - httpx
  - pytest
  - respx
key_decisions:
  - "Decided to scope ActionType.UNMONITOR to the specific media item level: individual episodes for TV shows via /api/v3/episode/monitor and movies via /api/v3/movie/editor."
  - "Replaced ActionType.UNMONITOR_EPISODE with ActionType.UNMONITOR_SERIES to provide explicit series-level unmonitoring via /api/v3/series/editor."
  - "Pruned UNMONITOR_SERIES on Movie items during plan simulation."
requirements_completed:
  - ACT-03
  - ACT-04
duration_minutes: 3
completed_date: "2026-08-24"
---

# Phase 07 Plan 01: Scope Unmonitor to Episodes and Add Unmonitor-Series Option Summary

## Executive Summary
Refactored unmonitor mutation action semantics across domain models, simulation engine, confirmation formatting, and Typer CLI options. The `--unmonitor` flag now granularly unmonitors matched items (individual episodes for TV series via `/api/v3/episode/monitor` and movies via `/api/v3/movie/editor`). The obsolete `--unmonitor-episode` flag was removed, and `--unmonitor-series` was added for explicitly unmonitoring entire TV series with automatic deduplication across episodes.

## Tasks Completed

| Task ID | Description | Commits |
|---|---|---|
| `07-01-01` | Update `ActionType` enum, `ActionExecutor` plan building & execution, and confirmation formatting | `8960a45` (`feat(07-01): scope unmonitor to episodes and add unmonitor_series action`) |
| `07-01-02` | Update CLI `clean` command options (`--unmonitor`, `--unmonitor-series`) and add integration tests | `9d82cc6` (`feat(07-01): update CLI clean options for unmonitor and unmonitor-series`) |

## Verification Results

- Unit test coverage in `tests/test_action_models.py` and `tests/test_action_executor.py` verifying item-level unmonitor and series unmonitor deduplication passed cleanly.
- Integration tests in `tests/test_cli_clean.py` verifying `--unmonitor`, `--unmonitor-series`, and error validation passed cleanly.
- Full automated test suite: 236/236 passed in 5.59s.
- Linters & static type checker: `ruff check .` and `mypy src/` passed with 0 errors.

## Artifacts Created / Modified

- `src/arr_oldies/actions/models.py`: Updated `ActionType` enum (`UNMONITOR`, `UNMONITOR_SERIES`).
- `src/arr_oldies/actions/executor.py`: Updated `build_plan` pruning and `execute_plan` ordering for scoped unmonitor and series unmonitor.
- `src/arr_oldies/cli.py`: Updated `clean` command arguments and action dispatch.
- `tests/test_action_models.py`: Updated `ActionType` enum assertions.
- `tests/test_action_executor.py`: Updated unit tests for unmonitor scoping and series unmonitoring.
- `tests/test_cli_clean.py`: Updated CLI clean integration tests.
