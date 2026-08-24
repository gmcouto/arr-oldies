---
phase: 05-safe-action-engine-dry-run-deletion-unmonitoring
plan: 01
subsystem: actions
tags:
  - actions
  - dry-run
  - simulation
  - radarr
  - sonarr
  - unmonitor
  - delete
requires:
  - phase: 04-full-inventory-audit-sorting-reporting
    provides: Unified MediaInventoryItem schema and filtering engine
provides:
  - Action domain models (ActionType, ActionItem, ActionPlan, ActionResult, ExecutionReport)
  - RadarrClient and SonarrClient mutation REST endpoints
  - ActionExecutor simulation planning and dry-run JSON serialization
  - ActionExecutor ordered mutation execution with deduplication and error resilience
affects:
  - src/arr_oldies/actions/models.py
  - src/arr_oldies/actions/executor.py
  - src/arr_oldies/actions/__init__.py
  - src/arr_oldies/api/radarr.py
  - src/arr_oldies/api/sonarr.py
tech-stack:
  added: []
  patterns:
    - Immutable ActionPlan simulation objects with dry_run default
    - Strict unmonitor-before-delete mutation execution order
    - Deduplicated series-level unmonitoring across multiple episodes
    - Per-item error isolation in batch executions
key-files:
  created:
    - src/arr_oldies/actions/models.py
    - src/arr_oldies/actions/executor.py
    - src/arr_oldies/actions/__init__.py
    - tests/test_action_models.py
    - tests/test_radarr_client_actions.py
    - tests/test_sonarr_client_actions.py
    - tests/test_action_executor.py
  modified:
    - src/arr_oldies/api/radarr.py
    - src/arr_oldies/api/sonarr.py
key-decisions:
  - "Enforced unmonitoring preceding file deletion in ActionExecutor to avoid indexer redownload races"
  - "Deduplicated series-level unmonitoring in ActionExecutor to minimize redundant PUT calls to Sonarr"
  - "Isolated single-item API failures during batch execution to prevent 500 errors on one file from halting other deletions"
requirements-completed:
  - ACT-01
  - ACT-02
  - ACT-03
  - ACT-04
  - ACT-05
duration: 4 min
completed: 2026-08-24T00:54:50Z
coverage:
  - deliverable: Action Domain Schemas (Pydantic v2)
    verification:
      kind: test
      ref: tests/test_action_models.py
      status: pass
    human_judgment: false
  - deliverable: Radarr & Sonarr Mutation Client Methods
    verification:
      kind: test
      ref: tests/test_radarr_client_actions.py, tests/test_sonarr_client_actions.py
      status: pass
    human_judgment: false
  - deliverable: Action Planning & Dry-Run Serializer
    verification:
      kind: test
      ref: tests/test_action_executor.py#test_build_plan_defaults, tests/test_action_executor.py#test_export_plan_json
      status: pass
    human_judgment: false
  - deliverable: Ordered Mutation Engine with Deduplication & Error Resilience
    verification:
      kind: test
      ref: tests/test_action_executor.py#test_execute_plan_deletions_and_unmonitoring, tests/test_action_executor.py#test_execute_plan_error_resilience
      status: pass
    human_judgment: false
---

# Phase 05 Plan 01: Action Models, Mutation API Endpoints, and Execution Engine Summary

Action domain models (`ActionType`, `ActionItem`, `ActionPlan`, `ActionResult`, `ExecutionReport`), Radarr & Sonarr v3/v4 mutation endpoints, dry-run simulation planning, and safe ordered mutation execution engine implemented in `arr_oldies.actions`.

## Accomplishments

1. **Action Domain Models**: Implemented `ActionType` StrEnum (`delete`, `unmonitor`, `unmonitor_episode`, `remove`), `ActionItem`, `ActionPlan` (immutable dry-run plan), `ActionResult`, and `ExecutionReport` using Pydantic v2 schemas.
2. **Radarr & Sonarr Mutation REST Endpoints**:
   - `RadarrClient`: Added `delete_movie_file`, `unmonitor_movie` (`/api/v3/movie/editor`), and `delete_movie` (`/api/v3/movie/{id}`).
   - `SonarrClient`: Added `delete_episode_file`, `unmonitor_series` (`/api/v3/series/editor`), `unmonitor_episodes` (`/api/v3/episode/monitor`), and `delete_series` (`/api/v3/series/{id}`).
3. **ActionExecutor Simulation Planner**:
   - `build_plan`: Constructs `ActionPlan` with dry-run default, pruning inapplicable actions (e.g. episode unmonitoring on movies) and aggregating space/instance metrics without issuing network calls.
   - `export_plan_json`: Serializes `ActionPlan` into clean, schema-compliant JSON with human-readable size formatting.
4. **Safe Ordered Mutation Execution Engine**:
   - `execute_plan`: Executes unmonitoring before file deletion (to prevent *arr auto-redownload races), deduplicates series unmonitoring across multiple episodes of the same show, and catches per-item API failures without aborting the batch.
   - `export_report_json`: Serializes `ExecutionReport` to structured JSON.

## Verification

All 19 test cases in `tests/test_action_models.py`, `tests/test_radarr_client_actions.py`, `tests/test_sonarr_client_actions.py`, and `tests/test_action_executor.py` passed with 100% green status.

## Self-Check: PASSED
- `src/arr_oldies/actions/models.py` exists on disk
- `src/arr_oldies/actions/executor.py` exists on disk
- `src/arr_oldies/actions/__init__.py` exists on disk
- 19/19 tests pass
