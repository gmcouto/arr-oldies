---
phase: "01"
plan: "02"
subsystem: "cli-targeting-prober"
tags:
  - cli
  - typer
  - rich
  - httpx
  - respx
  - prober
  - targeting
requires:
  - "01-01"
provides:
  - "Instance targeting resolution with --radarr, --sonarr, and -i flags"
  - "Conflict detection for incompatible instance targeting flags"
  - "Concurrent async HTTPX health prober querying /api/v3/system/status"
  - "Rich table formatting and styled welcome banner"
  - "Typer CLI application with validate-config command and exit codes 0/1/2"
affects:
  - "All downstream commands (API history client, scan, action engine)"
tech-stack:
  added:
    - "types-PyYAML"
  patterns:
    - "Concurrent asyncio.gather probing via HTTPX"
    - "High-contrast Rich table formatting"
    - "Clean stderr error routing with separate stdout tables"
key-files:
  created:
    - "src/arr_oldies/targeting.py"
    - "src/arr_oldies/prober.py"
    - "src/arr_oldies/console.py"
    - "src/arr_oldies/cli.py"
    - "tests/test_targeting.py"
    - "tests/test_prober.py"
    - "tests/test_cli.py"
  modified:
    - "pyproject.toml"
key-decisions:
  - "Target all configured instances by default when no flags are supplied [D-09]"
  - "Reject conflicting instance targeting combinations with exit code 2 [D-10, D-14]"
  - "Probe instances concurrently using asyncio.gather against /api/v3/system/status [D-05, D-07]"
  - "Translate network errors and HTTP 401/403/404 into user-friendly diagnostic messages [D-08]"
  - "Render results in high-contrast Rich table with millisecond latencies [D-06]"
  - "Exit with code 0 on all-success, code 1 on probe failure, and code 2 on configuration/targeting error [D-13, D-14]"
requirements-completed:
  - CONF-02
  - CONF-03
duration: "2 min"
completed: "2026-08-23T23:19:30Z"
coverage:
  - deliverable: "Instance targeting engine with --radarr, --sonarr, -i, and conflict detection"
    verification:
      kind: "test"
      ref: "tests/test_targeting.py"
      status: "pass"
    human_judgment: false
  - deliverable: "Async concurrent HTTPX health prober with latency measurement and error translations"
    verification:
      kind: "test"
      ref: "tests/test_prober.py"
      status: "pass"
    human_judgment: false
  - deliverable: "Rich console rendering, welcome banner, and stderr diagnostic logging"
    verification:
      kind: "test"
      ref: "tests/test_cli.py"
      status: "pass"
    human_judgment: false
  - deliverable: "Typer CLI application with validate-config command and exit codes 0/1/2"
    verification:
      kind: "test"
      ref: "tests/test_cli.py"
      status: "pass"
    human_judgment: false
---

# Phase 01 Plan 02: Instance Targeting, Health Prober & CLI Validation Command Summary

Implemented instance target resolution with conflict detection, concurrent async HTTPX health probing against `/api/v3/system/status`, Rich terminal table presentation, and the complete Typer CLI application featuring the `validate-config` command with exit codes 0, 1, and 2.

## Accomplishments

1. **Instance Targeting & Conflict Engine (`targeting.py`)**: Implemented `resolve_target_instances` supporting default all-instances behavior, `--radarr` / `--sonarr` filtering, repeatable `-i / --instance` selection, and strict conflict detection (raising `InstanceConflictError` when `--radarr` is used with a Sonarr instance).
2. **Concurrent Health Prober (`prober.py`)**: Built `probe_single_instance` and `probe_all_instances` using `httpx.AsyncClient` and `asyncio.gather`. Measures round-trip latency in ms, extracts remote server version, and translates HTTP 401/403/404, timeouts, and connection refused errors into clean user messages.
3. **Rich Console Presentation (`console.py`)**: Added `render_validation_table` rendering high-contrast rounded tables with status badges, `render_banner` for bare CLI calls, `mask_secret` for credential safety, and `print_error` directing diagnostic errors to `stderr`.
4. **Typer CLI Application (`cli.py`)**: Configured the Typer application with global `--config`, `-v/--verbose`, and `--version` options, plus the `validate-config` command with exit codes 0 (all healthy), 1 (probe failure), and 2 (configuration/targeting error).
5. **Comprehensive Test Suite**: Added 24 new unit and integration tests across `test_targeting.py`, `test_prober.py` (with `respx`), and `test_cli.py` (with `CliRunner`), bringing the test suite to 39 passing tests with 100% green coverage.

## Deviations from Plan

None - plan executed exactly as written.

## Self-Check: PASSED
