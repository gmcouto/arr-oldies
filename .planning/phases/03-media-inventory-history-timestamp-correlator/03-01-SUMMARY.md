---
phase: 03-media-inventory-history-timestamp-correlator
plan: 01
subsystem: inventory
tags:
  - pydantic
  - iso-639
  - language-normalizer
  - unit-parsers
  - timezone-normalization
requires:
  - 02-async-arr-api-clients-batch-history-fetcher
provides:
  - src/arr_oldies/inventory/models.py
  - src/arr_oldies/inventory/languages.py
  - src/arr_oldies/inventory/parser.py
  - src/arr_oldies/inventory/__init__.py
  - src/arr_oldies/exceptions.py
  - src/arr_oldies/constants.py
affects:
  - 03-02
  - 03-03
tech-stack:
  added: []
  patterns:
    - Pydantic v2 unified `MediaInventoryItem` data model with UTC timezone awareness enforcement
    - Fast canonical ISO-639 language resolver with bidirectional synonym dictionary lookup
    - Multi-delimiter regex splitting (`/`, `,`, `+`, `|`, `;`, `\`) for audio stream metadata
    - Robust regex-based unit string parsers (`parse_size`, `parse_age_cutoff`, `parse_date_cutoff`) with typed `ParseError` domain exceptions
key-files:
  created:
    - src/arr_oldies/inventory/__init__.py
    - src/arr_oldies/inventory/models.py
    - src/arr_oldies/inventory/languages.py
    - src/arr_oldies/inventory/parser.py
    - tests/test_inventory_models.py
    - tests/test_language_normalizer.py
    - tests/test_parser.py
  modified:
    - src/arr_oldies/constants.py
    - src/arr_oldies/exceptions.py
key-decisions:
  - "Enforced UTC timezone awareness on all datetime fields (`import_date`, `grab_date`) via `@field_validator(mode='after')` and `parse_date_cutoff` to eliminate offset-naive comparison failures [T-03-02]"
  - "Built canonical ISO-639 resolution with bidirectional synonym matching allowing queries like `ja`, `jpn`, `japanese`, or `jap` to match Japanese audio tracks"
  - "Applied anchored regex validation and explicit multiplier mappings for size and age strings to prevent denial-of-service or invalid numeric conversions [T-03-01]"
requirements-completed:
  - INVT-02
  - INVT-03
  - INVT-05
duration: 3 min
completed: 2026-08-24T00:03:00Z
coverage:
  - deliverable: "Pydantic v2 MediaInventoryItem, InventoryFilter, and InventorySummary data models"
    verification:
      kind: automated
      ref: tests/test_inventory_models.py
      status: pass
    human_judgment: false
  - deliverable: "LanguageNormalizer ISO-639 extraction and bidirectional synonym matching engine"
    verification:
      kind: automated
      ref: tests/test_language_normalizer.py
      status: pass
    human_judgment: false
  - deliverable: "parse_size, parse_age_cutoff, and parse_date_cutoff string parsing utilities"
    verification:
      kind: automated
      ref: tests/test_parser.py
      status: pass
    human_judgment: false
  - deliverable: "Subsystem package exports and model serialization verification"
    verification:
      kind: automated
      ref: tests/test_inventory_models.py#test_package_reexports
      status: pass
    human_judgment: false
---

# Phase 03 Plan 01: Media Inventory Data Models, Language Normalizer & Human String Parsers Summary

Established the foundational data models, exception hierarchy, ISO-639 audio language normalization engine, and human-friendly string parsing utilities required for media inventory correlation and filtering.

## Accomplishments

1. **Inventory Domain Exceptions (`src/arr_oldies/exceptions.py`)**:
   - Added `InventoryError(ArrOldiesError)` as the base inventory exception.
   - Added `ParseError(ArrOldiesError)` for user input parsing failures.
   - Added `CorrelationError(InventoryError)` for metadata correlation failures.

2. **Unified Pydantic v2 Inventory Models (`src/arr_oldies/inventory/models.py`)**:
   - Implemented `MediaType`, `HistoryStatus`, `SortKey`, and `SortDirection` enums.
   - Built `MediaInventoryItem` unified model with UTC timezone validation (`ensure_utc` validator converting naive or tz-aware datetimes to UTC).
   - Built `InventoryFilter` and `InventorySummary` models for downstream filtering and reporting.

3. **ISO-639 Language Normalization Engine (`src/arr_oldies/inventory/languages.py`)**:
   - Created `LanguageEntry` frozen dataclass and `LanguageNormalizer` resolver with canonical ISO-639 mapping table and synonym lookups.
   - Implemented `extract_languages()` handling multiple delimiters (`/`, `,`, `+`, `|`, `;`, `\`), stripping formatting tokens, and deduplicating preserving first encounter order.
   - Implemented `matches()` providing bidirectional matching across ISO-639-1, ISO-639-2, ISO-639-3, English names, and synonyms (e.g. `ja`, `jpn`, `japanese`, `jap`).

4. **Human String Parsers (`src/arr_oldies/inventory/parser.py`)**:
   - Implemented `parse_size()` converting human size strings (e.g., `500MB`, `2GB`, `1.5GiB`, `100M`) to integer bytes with decimal and binary multiplier support.
   - Implemented `parse_age_cutoff()` converting interval strings (e.g., `30d`, `6m`, `1y`, `2w`, `90`) to exact integer days.
   - Implemented `parse_date_cutoff()` parsing `YYYY-MM-DD` and ISO-8601 strings into UTC timezone-aware `datetime` objects.
   - Raised typed `ParseError` on invalid formats.

5. **Package Re-exports & Test Verification (`src/arr_oldies/inventory/__init__.py`)**:
   - Cleanly exported all models, enums, normalizers, and parser utilities via `__all__`.
   - Built comprehensive test suites (`tests/test_language_normalizer.py`, `tests/test_parser.py`, `tests/test_inventory_models.py`) totaling 60 automated unit tests (130 passing across the entire repository).

## Deviations from Plan

None - plan executed exactly as written.

## Verification

```bash
.venv/bin/pytest tests/test_language_normalizer.py tests/test_parser.py tests/test_inventory_models.py -v
```
All 60 tests passed in 0.19s. Full test suite (130 tests) passed in 1.24s.

## Self-Check: PASSED
- `src/arr_oldies/inventory/models.py` exists: YES
- `src/arr_oldies/inventory/languages.py` exists: YES
- `src/arr_oldies/inventory/parser.py` exists: YES
- `src/arr_oldies/inventory/__init__.py` exists: YES
- `tests/test_inventory_models.py` exists: YES
- `tests/test_language_normalizer.py` exists: YES
- `tests/test_parser.py` exists: YES
- Commits `3babade`, `abd58c0`, `2c7ce30`, and `8526409` recorded: YES
- Full test suite passes 100%: YES
