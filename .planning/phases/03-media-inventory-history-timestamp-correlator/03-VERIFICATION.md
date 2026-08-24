---
status: passed
phase: 03-media-inventory-history-timestamp-correlator
verified: 2026-08-24T03:07:30Z
requirements:
  INVT-01: pass
  INVT-02: pass
  INVT-03: pass
  INVT-04: pass
  INVT-05: pass
  INVT-06: pass
score: 6/6
---

# Phase 03: Media Inventory & History Timestamp Correlator — Verification Report

## Goal Verification

**Phase Goal:** Correlate media files with History API download/import timestamps and provide unified inventory records with ISO-639 audio language filtering, deterministic oldest-first sorting, legacy media fallbacks, and multi-dimensional filter predicates.

### Requirement Traceability Matrix

| Requirement ID | Description | Status | Verification Reference |
|---|---|---|---|
| **INVT-01** | Correlate Radarr movie and Sonarr episode files (including multi-episode files) with exact History API download/import and grab event timestamps | PASS | `tests/test_correlator_radarr.py`, `tests/test_correlator_sonarr.py` |
| **INVT-02** | Parse and normalize audio languages from mediaInfo into standardized ISO-639 representations supporting delimiter splitting and bidirectional matching | PASS | `tests/test_language_normalizer.py` |
| **INVT-03** | Unified `MediaInventoryItem` data model across Radarr and Sonarr capturing file metadata, UTC timestamps, age calculations, and summary metrics | PASS | `tests/test_inventory_models.py`, `tests/test_inventory_engine.py` |
| **INVT-04** | Sort media inventory deterministically by oldest import date (default), oldest grab date, size, title, or age with stable tie-breaking | PASS | `tests/test_inventory_engine.py` |
| **INVT-05** | Filter inventory by audio language, media type, instance name, size bounds, age bounds, and date cutoffs with human string parsers | PASS | `tests/test_parser.py`, `tests/test_inventory_engine.py`, `tests/test_inventory_integration.py` |
| **INVT-06** | Graceful fallback for legacy media items with pruned or empty history logs to `file.date_added` with `is_legacy=True` without failing scans | PASS | `tests/test_correlator_legacy.py`, `tests/test_inventory_integration.py` |

---

## Must-Haves Verification

1. **Unified Data Models & UTC Datetime Normalization [INVT-03, T-03-02]**:
   - `MediaInventoryItem` encapsulates movie and TV episode records.
   - `@field_validator('import_date', 'grab_date', mode='after')` normalizes naive and timezone-aware datetimes to UTC.
   - `InventoryFilter` and `InventorySummary` models correctly represent queries and aggregate metrics.
   - Verified via `tests/test_inventory_models.py` (9 passed).

2. **Language Normalization Engine [INVT-02, INVT-05]**:
   - `LanguageNormalizer` splits compound audio language strings (`/`, `,`, `+`, `|`, `;`, `\`) and cleans bracketed tokens (`[EN+DE]`).
   - Resolves ISO-639-1, ISO-639-2, ISO-639-3 codes, canonical English names, and synonyms.
   - Bidirectional matching in `matches()` enables queries like `--audio-lang ja`, `jpn`, or `japanese` to match Japanese audio tracks.
   - Verified via `tests/test_language_normalizer.py` (21 passed).

3. **Human Unit String Parsers [INVT-05, T-03-01, T-03-02]**:
   - `parse_size()` parses binary and decimal size strings (`500MB`, `2GB`, `1.5GiB`, `100M`) into byte integers.
   - `parse_age_cutoff()` parses age interval strings (`30d`, `6m`, `1y`, `2w`, `90`) into integer days.
   - `parse_date_cutoff()` parses `YYYY-MM-DD` and ISO-8601 strings into UTC timezone-aware datetimes.
   - Verified via `tests/test_parser.py` (30 passed).

4. **History Event Indexing & Correlation [INVT-01, T-03-03, T-03-04]**:
   - `RadarrHistoryIndex` and `SonarrHistoryIndex` build multi-key hash maps in $O(N+M)$ time.
   - `HistoryCorrelator` resolves exact `downloadFolderImported` / `movieFileImported` / `episodeFileImported` events and `grabbed` events.
   - Multi-episode TV files format badges accurately (`S01E01-E02`).
   - Verified via `tests/test_correlator_radarr.py` (4 passed), `tests/test_correlator_sonarr.py` (3 passed).

5. **Legacy Media Fallback [INVT-06, T-03-05]**:
   - Files without history records fall back to `date_added` with `is_legacy=True`, `has_history=False`, `history_status=HistoryStatus.LEGACY`, and `grab_date=None`.
   - Age calculation and inventory aggregation work seamlessly without runtime errors.
   - Verified via `tests/test_correlator_legacy.py` (2 passed).

6. **Inventory Filtering, Sorting & Summary Engine [INVT-03, INVT-04, INVT-05]**:
   - `InventoryEngine.filter_inventory` evaluates multi-dimensional predicates in a single pass.
   - `InventoryEngine.sort_inventory` deterministically sorts by import date, grab date, size, title, or age with stable tie-breaking.
   - `InventoryEngine.generate_summary` produces accurate statistical summaries.
   - Verified via `tests/test_inventory_engine.py` (9 passed).

7. **End-to-End Multi-Instance Integration Pipeline [INVT-01..06]**:
   - Verified across mixed Radarr (4K, HD legacy) and Sonarr (anime, TV) instance datasets.
   - Full pipeline correlation, filtering by size/age/language, sorting, and summary metrics pass completely.
   - Verified via `tests/test_inventory_integration.py` (1 passed).

---

## Test Suite Execution Summary

```
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.1.1, pluggy-1.6.0
rootdir: /mnt/zfspool/appdata/code-server/workspace/arr-oldies
configfile: pyproject.toml
testpaths: tests
plugins: anyio-4.14.2, respx-0.23.1, asyncio-1.4.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 149 items

tests/test_api_models.py .....                                           [  3%]
tests/test_base_client.py ..........                                     [ 10%]
tests/test_cli.py .........                                              [ 16%]
tests/test_config.py .........                                           [ 22%]
tests/test_correlator_legacy.py ..                                       [ 23%]
tests/test_correlator_radarr.py ....                                     [ 26%]
tests/test_correlator_sonarr.py ...                                      [ 28%]
tests/test_history_fetcher.py .....                                      [ 31%]
tests/test_inventory_engine.py .........                                 [ 37%]
tests/test_inventory_integration.py .                                    [ 38%]
tests/test_inventory_models.py .........                                 [ 44%]
tests/test_language_normalizer.py .....................                  [ 58%]
tests/test_models.py ......                                              [ 62%]
tests/test_parser.py ..............................                      [ 82%]
tests/test_prober.py ......                                              [ 86%]
tests/test_radarr_client.py ......                                       [ 90%]
tests/test_sonarr_client.py .....                                        [ 93%]
tests/test_targeting.py .........                                        [100%]

============================= 149 passed in 1.04s ==============================
```

## Gaps
None.

## Human Verification Needed
None. All data modeling, language normalization, string parsing, history correlation, legacy fallback, filtering, and sorting behaviors are 100% verified via automated unit and integration test fixtures.
