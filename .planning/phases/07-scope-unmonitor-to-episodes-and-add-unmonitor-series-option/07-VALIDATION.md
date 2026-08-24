---
phase: 07
phase_slug: scope-unmonitor-to-episodes-and-add-unmonitor-series-option
created: 2026-08-24
---

# Phase 07: Scope unmonitor to episodes and add unmonitor-series option — Validation Strategy

## 1. Scope & Objective
Validate that:
1. `--unmonitor` flag unmonitors movies in Radarr and individual episodes in Sonarr for matched media files.
2. `--unmonitor-episode` is removed.
3. `--unmonitor-series` is added to explicitly unmonitor the entire parent series in Sonarr.
4. Action plans, dry-run simulation, execution reports, and CLI help reflect these changes.

## 2. Automated Test Matrix

| Layer | Target | Test File | Verification Command |
|---|---|---|---|
| Domain Models | `ActionType` enum values | `tests/test_action_models.py` | `.venv/bin/pytest tests/test_action_models.py` |
| Action Executor | Plan building & execution (item unmonitor vs series unmonitor) | `tests/test_action_executor.py` | `.venv/bin/pytest tests/test_action_executor.py` |
| CLI Clean | CLI arguments `--unmonitor` and `--unmonitor-series` | `tests/test_cli_clean.py` | `.venv/bin/pytest tests/test_cli_clean.py` |
| Full Suite | Cross-module regression prevention | All tests | `.venv/bin/pytest -v` |
| Linters & Types | Code quality and type safety | `src/`, `tests/` | `ruff check . && mypy src/` |

## 3. Exit Criteria
- 100% test pass rate across all unit and integration tests.
- 0 lint errors, 0 type errors.
