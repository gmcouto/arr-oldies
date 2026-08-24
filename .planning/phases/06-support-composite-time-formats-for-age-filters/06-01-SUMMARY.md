---
phase: 06-support-composite-time-formats-for-age-filters
plan: 01
subsystem: inventory
tags: [parser, age-filters, composite-formats, cli, typer, pytest]

requires:
  - phase: 02-inventory-pipeline-and-filtering-engine
    provides: Inventory models, filtering engine, and initial parse_age_cutoff implementation
provides:
  - Enhanced parse_age_cutoff supporting composite duration strings (e.g. '1y1m1d', '2y6m', '3w4d') with delimiter tolerance
  - Updated CLI help strings for --older-than and --newer-than options in scan and clean commands
  - Comprehensive unit and integration test coverage for single and composite age filters
affects: [cli, inventory, actions]

actuals:
  tokens: 4200
  tasks: 2
  commits: 2

tech-stack:
  added: []
  patterns:
    - Regex tokenization and span delimiter checking for multi-unit human interval parsing

key-files:
  created: []
  modified:
    - src/arr_oldies/inventory/parser.py
    - src/arr_oldies/cli.py
    - tests/test_parser.py
    - tests/test_cli_scan.py
    - tests/test_cli_clean.py

key-decisions:
  - "Support flexible delimiters (whitespace, commas, 'and', '&') between composite time tokens while rejecting unrecognized characters or units"
  - "Standardize unit conversions to 365 days/year, 30 days/month, 7 days/week, 1 day/day"

patterns-established:
  - "Multi-token string parsing using finditer with span-gap delimiter validation"

requirements-completed:
  - INVT-05

coverage:
  - id: D1
    description: "Composite relative age format tokenization and day accumulation in parse_age_cutoff"
    requirement: "INVT-05"
    verification:
      - kind: unit
        ref: "tests/test_parser.py#test_parse_age_cutoff_valid"
        status: pass
      - kind: unit
        ref: "tests/test_parser.py#test_parse_age_cutoff_invalid"
        status: pass
    human_judgment: false
  - id: D2
    description: "CLI scan and clean command integration for composite --older-than and --newer-than filters"
    requirement: "INVT-05"
    verification:
      - kind: integration
        ref: "tests/test_cli_scan.py#test_cli_scan_composite_age_filters"
        status: pass
      - kind: integration
        ref: "tests/test_cli_clean.py#test_cli_clean_composite_age_filters"
        status: pass
    human_judgment: false

duration: 4 min
completed: 2026-08-24
status: complete
---

# Phase 06 Plan 01: Support Composite Time Formats for Age Filters Summary

**Tokenized composite time interval parser supporting compound durations like `1y1m1d`, `2y6m`, and `3w4d` with delimiter validation and CLI integration across scan and clean commands**

## Performance

- **Duration:** 4 min
- **Started:** 2026-08-24T09:59:00Z
- **Completed:** 2026-08-24T10:03:00Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Upgraded `parse_age_cutoff` in `src/arr_oldies/inventory/parser.py` to tokenize compound durations (`1y1m1d`, `2y6m`, `1 year 1 month 1 day`, `1y & 3w`) into cumulative integer days while preserving single-unit backward compatibility (`30`, `30d`, `6m`, `1y`).
- Implemented strict span delimiter checks rejecting malformed tokens or unrecognized characters with descriptive `ParseError` exceptions.
- Updated Typer CLI help strings in `src/arr_oldies/cli.py` across `scan` and `clean` commands.
- Added comprehensive unit tests in `tests/test_parser.py` and end-to-end CLI integration tests in `tests/test_cli_scan.py` and `tests/test_cli_clean.py`.

## Task Commits

Each task was committed atomically:

1. **Task 1: Extend parse_age_cutoff to support composite time formats and update unit tests** - `efee30d` (feat)
2. **Task 2: Update CLI documentation and add end-to-end composite age filter integration tests** - `92d17fb` (feat)

## Files Created/Modified

- `src/arr_oldies/inventory/parser.py` - Tokenized composite duration parsing and validation
- `src/arr_oldies/cli.py` - Updated CLI option help text for `--older-than` / `--newer-than`
- `tests/test_parser.py` - Parametrized unit tests for single, composite, delimited, and invalid duration strings
- `tests/test_cli_scan.py` - CLI scan integration tests validating composite age filters
- `tests/test_cli_clean.py` - CLI clean integration tests validating composite age filters in dry-run and execute modes

## Decisions Made

- Supported optional flexible delimiters between tokens (spaces, commas, 'and', '&') while enforcing strict rejection of invalid trailing characters or unknown unit identifiers.
- Preserved standard conversions: 1y = 365d, 1m = 30d, 1w = 7d, 1d = 1d.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- All phase 06 requirements (INVT-05) satisfied and verified across unit and CLI integration tests.
- Full test suite passing (236/236 tests).

---
*Phase: 06-support-composite-time-formats-for-age-filters*
*Completed: 2026-08-24*
