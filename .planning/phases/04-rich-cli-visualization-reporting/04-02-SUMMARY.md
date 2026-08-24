---
phase: 04-rich-cli-visualization-reporting
plan: 02
subsystem: cli
tags:
  - typer
  - json
  - scan
  - reporting
requires:
  - phase: 04-rich-cli-visualization-reporting
    plan: 01
    provides: OutputFormat, render_inventory_table, render_summary_panel, format_size
provides:
  - build_json_payload and export_inventory_json in arr_oldies.reporting.json_export
  - Typer scan command in arr_oldies.cli
affects:
  - src/arr_oldies/cli.py
  - src/arr_oldies/reporting/
key-files:
  created:
    - src/arr_oldies/reporting/json_export.py
    - tests/test_reporting_json.py
    - tests/test_cli_scan.py
  modified:
    - src/arr_oldies/cli.py
    - src/arr_oldies/reporting/__init__.py
key-decisions:
  - "Enforced stdout purity in JSON mode using typer.echo to emit raw serialized JSON without Rich ANSI syntax highlighting or diagnostic pollution."
  - "Wrapped concurrent instance fetching in stderr_console.status spinner during table mode, while suppressing spinners in json mode."
  - "Integrated all Phase 2 and Phase 3 components (fetcher, correlator, engine, parser, targeting) cleanly into the scan CLI pipeline."
requirements-completed:
  - CLI-01
  - CLI-02
  - CLI-03
  - CLI-04
duration: 5 min
completed: 2026-08-24T03:31:50Z
coverage:
  - deliverable: "Pure JSON export serializer (build_json_payload, export_inventory_json)"
    verification:
      kind: test
      ref: tests/test_reporting_json.py#test_export_inventory_json_validity_and_purity
      status: pass
    human_judgment: false
  - deliverable: "CLI scan command with default table and summary rendering"
    verification:
      kind: test
      ref: tests/test_cli_scan.py#test_cli_scan_default_table_output
      status: pass
    human_judgment: false
  - deliverable: "CLI scan command with JSON output format"
    verification:
      kind: test
      ref: tests/test_cli_scan.py#test_cli_scan_format_json_pure_stdout
      status: pass
    human_judgment: false
  - deliverable: "Top-N output limit slicing with --limit"
    verification:
      kind: test
      ref: tests/test_cli_scan.py#test_cli_scan_limit_flag
      status: pass
    human_judgment: false
  - deliverable: "Multi-dimensional predicate filtering and sorting flags"
    verification:
      kind: test
      ref: tests/test_cli_scan.py#test_cli_scan_filtering_options
      status: pass
    human_judgment: false
---

# Phase 04 Plan 02: JSON Export Serializer and CLI `scan` Command Summary

Implemented the pure machine-readable JSON export serializer and the comprehensive `arr-oldies scan` CLI command integrating instance targeting, concurrent fetching, history timestamp correlation, predicate filtering, deterministic sorting, top-N limit slicing, and strict stdout/stderr stream isolation.

## Accomplishments

1. **Structured JSON Export (`json_export.py`, `__init__.py`)**:
   - Implemented `build_json_payload` creating structured dictionaries containing `metadata` (scan parameters, counts), `summary` (total items, storage metrics, date spans, space reclamation), and `items` (model dumped inventory records with human sizes).
   - Implemented `export_inventory_json` serializing payloads into pure JSON without ANSI escape sequences.

2. **CLI `scan` Command (`cli.py`)**:
   - Registered `@app.command("scan")` with targeting (`--radarr`, `--sonarr`, `-i`), filtering (`--type`, `--audio-lang`, `--min-size`, `--max-size`, `--older-than`, `--newer-than`, `--before`, `--after`, `--legacy`, `--history`), sorting (`--sort`, `--sort-dir`), output controls (`--limit`, `--format`, `--summary/--no-summary`).
   - Implemented the full execution pipeline: configuration loading -> instance resolution -> argument parsing -> concurrent async fetching -> history correlation -> filtering -> sorting -> metrics generation -> top-N slicing -> table/JSON rendering.
   - Enforced stream isolation: pure JSON on `stdout`, diagnostics and warnings on `stderr`.

3. **Integration & Regression Testing**:
   - Created 13 CLI integration tests in `tests/test_cli_scan.py` and 2 JSON tests in `tests/test_reporting_json.py`.
   - Verified 100% green status across all 175 project tests without regressions.

## Deviations from Plan

None - plan executed exactly as written.

## Self-Check: PASSED
