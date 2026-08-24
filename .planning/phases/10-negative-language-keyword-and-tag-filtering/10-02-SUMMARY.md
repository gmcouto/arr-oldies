---
phase: 10-negative-language-keyword-and-tag-filtering
plan: "02"
subsystem: cli
tags: [filtering, negative-language, title-matching, tags, clean, scan]

# Dependency graph
requires:
  - phase: 10-01
    provides: Tag model, get_tags client endpoints, MultiInstanceFetcher tag retrieval, and MediaInventoryItem.tags
provides:
  - Multi-predicated filtering in InventoryFilter and InventoryEngine
  - Negative audio language filtering (--!l, --not-audio-lang, etc.) [INVT-07]
  - Title substring filtering across movie, series, and episode titles (--title) [INVT-08]
  - Tag inclusion and exclusion filtering (--tag, --!tag, --exclude-tag) [INVT-09]
  - Updated README.md documentation and CLI help syntax
affects: [cli, reporting, actions]

# Actuals
actuals:
  tokens: 16000
  tasks: 2
  commits: 1

# Tech tracking
tech-stack:
  added: []
  patterns: [multi-predicated filtering pipeline, case-insensitive tag inclusion/exclusion sets, substring title search]

key-files:
  created: []
  modified:
    - src/arr_oldies/inventory/models.py
    - src/arr_oldies/inventory/engine.py
    - src/arr_oldies/cli.py
    - README.md
    - tests/test_inventory_models.py
    - tests/test_inventory_engine.py
    - tests/test_cli_scan.py
    - tests/test_cli_clean.py

key-decisions:
  - "Title substring matching searches both main item title and episode_title case-insensitively"
  - "Tag inclusion and exclusion normalize labels with lowercase stripping to prevent casing mismatch"
  - "Exposed intuitive CLI aliases (--not-audio-lang, --exclude-audio-lang, --not-lang, --exclude-tag, --not-tag) alongside short forms --!l and --!tag"

patterns-established:
  - "Case-insensitive substring search across movie, series, and episode titles"
  - "Case-insensitive set membership checks for tag inclusion and exclusion"

requirements-completed:
  - INVT-07
  - INVT-08
  - INVT-09

coverage:
  - id: D1
    description: "InventoryFilter supports not_audio_langs, titles, tags, and not_tags filter criteria"
    requirement: "INVT-07, INVT-08, INVT-09"
    verification:
      - kind: unit
        ref: "tests/test_inventory_models.py#test_inventory_item_and_filter_new_fields"
        status: pass
    human_judgment: false
  - id: D2
    description: "InventoryEngine filters out items matching not_audio_langs queries using LanguageNormalizer"
    requirement: "INVT-07"
    verification:
      - kind: unit
        ref: "tests/test_inventory_engine.py#test_filter_negative_audio_language"
        status: pass
    human_judgment: false
  - id: D3
    description: "InventoryEngine filters items by case-insensitive substring matching against movie, series, and episode titles"
    requirement: "INVT-08"
    verification:
      - kind: unit
        ref: "tests/test_inventory_engine.py#test_filter_title_substring_matching"
        status: pass
    human_judgment: false
  - id: D4
    description: "InventoryEngine filters items by case-insensitive tag inclusion (tags) and tag exclusion (not_tags)"
    requirement: "INVT-09"
    verification:
      - kind: unit
        ref: "tests/test_inventory_engine.py#test_filter_tag_inclusion_and_exclusion"
        status: pass
    human_judgment: false
  - id: D5
    description: "CLI scan and clean commands expose --!l, --title, --tag, and --!tag (with all aliases) and correctly populate InventoryFilter"
    requirement: "INVT-07, INVT-08, INVT-09"
    verification:
      - kind: integration
        ref: "tests/test_cli_scan.py#test_cli_scan_negative_language_and_title_filter"
        status: pass
      - kind: integration
        ref: "tests/test_cli_scan.py#test_cli_scan_tag_and_not_tag_filters"
        status: pass
      - kind: integration
        ref: "tests/test_cli_clean.py#test_cli_clean_with_negative_language_and_tag_flags"
        status: pass
    human_judgment: false
  - id: D6
    description: "Clean command dry-run and execute pipelines only target items matching the new filter options"
    requirement: "INVT-07, INVT-08, INVT-09"
    verification:
      - kind: integration
        ref: "tests/test_cli_clean.py#test_cli_clean_execution_with_tag_filter"
        status: pass
    human_judgment: false

# Metrics
duration: 5min
completed: 2026-08-24
status: complete
---

# Phase 10: Plan 02 Summary

**Negative audio language, title substring, and tag filtering in InventoryFilter, InventoryEngine, CLI commands, and README**

## Performance

- **Duration:** 5 min
- **Started:** 2026-08-24T19:44:20Z
- **Completed:** 2026-08-24T19:46:40Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments
- Added `not_audio_langs`, `titles`, `tags`, and `not_tags` optional list fields to `InventoryFilter`
- Implemented negative audio language filtering in `InventoryEngine.filter_inventory` using `LanguageNormalizer.matches` (INVT-07)
- Implemented case-insensitive title substring matching across movie title, series title, and episode title (INVT-08)
- Implemented case-insensitive tag inclusion and exclusion matching on `MediaInventoryItem.tags` (INVT-09)
- Exposed `--!l`, `--title`, `--tag`, and `--!tag` (with descriptive aliases `--not-audio-lang`, `--exclude-audio-lang`, `--not-lang`, `--exclude-tag`, `--not-tag`) across `scan` and `clean` CLI commands
- Updated `README.md` with complete documentation, usage examples, and flag descriptions for both `scan` and `clean` subcommands
- Added comprehensive unit and integration test coverage across models, engine, scan CLI, and clean action execution

## Task Commits

1. **Task 1 & 2: Negative language, title substring, and tag filters in engine and CLI** - `d14733c` (feat)

## Files Created/Modified
- `src/arr_oldies/inventory/models.py` - Extended InventoryFilter schema with not_audio_langs, titles, tags, not_tags
- `src/arr_oldies/inventory/engine.py` - Added 4 predicate filter evaluation steps in filter_inventory
- `src/arr_oldies/cli.py` - Added CLI flags and arguments to scan_command and clean_command
- `README.md` - Updated features, CLI examples, and option reference tables
- `tests/test_inventory_models.py` - Unit tests for InventoryFilter new fields
- `tests/test_inventory_engine.py` - Unit tests for negative language, title substring, tag inclusion/exclusion, and combined filters
- `tests/test_cli_scan.py` - Integration tests for scan with --!l, --title, --tag, --!tag
- `tests/test_cli_clean.py` - Integration tests for clean dry-run and mutation execution with new filters

## Decisions Made
- Title substring queries search both the primary title and `episode_title` (if present) case-insensitively, supporting broad matching across TV show episodes and movies.
- Tag inclusion and exclusion perform set comparisons after lowercase normalization and whitespace stripping to ensure accurate matching against user inputs.

## Deviations from Plan
None - plan executed exactly as written.

## Issues Encountered
None.

## Next Phase Readiness
- All requirements (INVT-07, INVT-08, INVT-09) for Phase 10 are completely fulfilled and tested. Ready for phase verification and closure.

---
*Phase: 10-negative-language-keyword-and-tag-filtering*
*Completed: 2026-08-24*
