# Phase 8: Support --monitored and --unmonitored filter for scan and clean - Research Report

## 1. Executive Summary & User Intent

### Goal
Enable filtering media items by monitored status across Radarr movies and Sonarr episodes in `scan` and `clean` commands using `--monitored` (with aliases `--only-monitored`, `--monitored-only`) and `--unmonitored` (with aliases `--only-unmonitored`, `--unmonitored-only`).

### User Value
1. **Targeted Cleanup & Auditing**: Users can isolate media files that are still being monitored by Radarr/Sonarr versus files already unmonitored.
2. **Safe & Redundancy-Free Unmonitoring**: Running `clean --unmonitor --only-monitored` allows users to identify and unmonitor only active items, eliminating redundant API unmonitor calls on items already unmonitored.
3. **Storage Reclamation of Abandoned/Unmonitored Media**: Users can find unmonitored media files taking up disk space (`scan --unmonitored` or `clean --delete --unmonitored`) to clean up abandoned downloads.

---

## 2. Codebase & Component Analysis

### A. API Models (`src/arr_oldies/api/models.py`)
- **Current State**:
  - `RadarrMovie`: already defines `monitored: bool = Field(default=True)` (line 57).
  - `SonarrSeries`: already defines `monitored: bool = Field(default=True)` (line 104).
  - `SonarrSeason`: already defines `monitored: bool = Field(default=True)` (line 93).
  - `SonarrEpisode`: already defines `monitored: bool = Field(default=True)` (line 133).
- **Deserialization**:
  - Models inherit from `ApiBaseModel` with `extra="ignore", populate_by_name=True`.
  - Both Radarr `/api/v3/movie` and Sonarr `/api/v3/episode` / `/api/v3/series` API responses return `monitored: bool` at root object levels.
  - No changes needed to `api/models.py`.

### B. Media Inventory Models (`src/arr_oldies/inventory/models.py`)
- **`MediaInventoryItem`**:
  - Currently lacks a `monitored` field.
  - **Proposed Change**: Add `monitored: bool = True` (with default `True` to preserve backward compatibility for tests and legacy fixtures).
- **`InventoryFilter`**:
  - Currently has `legacy_only: bool = False`, `history_only: bool = False`, etc.
  - **Proposed Change**: Add:
    - `monitored_only: bool = False` (filter only monitored items)
    - `unmonitored_only: bool = False` (filter only unmonitored items)
- **`InventorySummary`**:
  - Can optionally track `monitored_count: int = 0` and `unmonitored_count: int = 0` if desired for summary metrics.

### C. History Correlator (`src/arr_oldies/inventory/correlator.py`)
- **`_correlate_radarr`**:
  - Currently has access to `movie = movies_by_id.get(movie_file.movie_id)`.
  - Resolve monitored status:
    ```python
    monitored = movie.monitored if movie is not None else True
    ```
  - Pass `monitored=monitored` when creating `MediaInventoryItem`.
- **`_correlate_sonarr`**:
  - Currently builds `episodes = episodes_by_file_id.get(ep_file.id, [])` and has `series = series_by_id.get(ep_file.series_id)`.
  - Episode file monitored status resolution:
    - If `episodes` is non-empty: `any(ep.monitored for ep in episodes)`.
      *Why `any` instead of `all`*: In Sonarr, a media file covering multiple episodes is actively monitored if any episode within it is monitored.
    - If `episodes` is empty (e.g., unlinked/orphan file): fallback to `series.monitored if series is not None else True`.
  - Pass `monitored=monitored` when creating `MediaInventoryItem`.

### D. Inventory Engine (`src/arr_oldies/inventory/engine.py`)
- **`filter_inventory`**:
  - Add monitored filter step:
    ```python
    if criteria.monitored_only and not item.monitored:
        continue
    if criteria.unmonitored_only and item.monitored:
        continue
    ```
- **`generate_summary`**:
  - Summary aggregation computes item monitored breakdown if included in `InventorySummary`.

### E. Typer CLI Entrypoints (`src/arr_oldies/cli.py`)
- **Commands affected**: `scan` and `clean`.
- **CLI Options to add to both `scan` and `clean`**:
  ```python
  monitored: Annotated[
      bool,
      typer.Option(
          "--monitored",
          "--monitored-only",
          "--only-monitored",
          help="Filter only monitored media items.",
      ),
  ] = (False,)
  unmonitored: Annotated[
      bool,
      typer.Option(
          "--unmonitored",
          "--unmonitored-only",
          "--only-unmonitored",
          help="Filter only unmonitored media items.",
      ),
  ] = (False,)
  ```
- **Mutual Exclusion Check**:
  ```python
  if monitored and unmonitored:
      print_error("Cannot specify both --monitored and --unmonitored filter flags.")
      raise typer.Exit(code=EXIT_CONFIG_ERROR)
  ```
- **Pass to `InventoryFilter`**:
  ```python
  criteria = InventoryFilter(
      ...,
      monitored_only=monitored,
      unmonitored_only=unmonitored,
  )
  ```

### F. Reporting & Formatting (`src/arr_oldies/reporting/`)
- **`json_export.py`**:
  - Serializes `MediaInventoryItem` with `item.model_dump(mode="json")`. With `monitored: bool` in `MediaInventoryItem`, it automatically includes `"monitored": true/false` in each item's JSON export.
- **`table.py` / `formatters.py`**:
  - In `render_inventory_table`, item monitored state can be surfaced in title metadata or badges if unmonitored.

---

## 3. Pitfalls & Edge Cases

1. **Multi-Episode Files with Split Monitored States**:
   - Scenario: Multi-episode file containing `[S01E01, S01E02]`, where E01 is monitored and E02 is unmonitored.
   - Handling: `any(ep.monitored for ep in episodes)` marks the file item as `monitored=True`. When `--unmonitor` action is executed, it will unmonitor the remaining monitored episode(s) via `/api/v3/episode/monitor`.
2. **Missing Metadata / Orphan Files**:
   - Scenario: Radarr movie file without matching `RadarrMovie` in `movies_by_id`, or Sonarr episode file without matching `episodes`.
   - Handling: Default safely to `True` for movie (or series monitored flag for Sonarr) without throwing `AttributeError` / `KeyError`.
3. **Conflicting Filter Flags**:
   - Scenario: User invokes `arr-oldies scan --monitored --unmonitored`.
   - Handling: Validate in `cli.py` before querying API / running filters, emit `print_error("Cannot specify both --monitored and --unmonitored filter flags.")`, and exit with code `EXIT_CONFIG_ERROR` (`2`).
4. **Flag Aliases Consistency**:
   - Users might intuitively type `--monitored`, `--only-monitored`, or `--monitored-only`, as well as `--unmonitored`, `--only-unmonitored`, or `--unmonitored-only`.
   - Handling: Define all aliases in Typer `Option(...)` so that all variations work seamlessly without confusion.
5. **Clean Action Synergy**:
   - Running `clean --unmonitor --only-monitored` or `clean --unmonitor-series --only-monitored`:
   - Filters out unmonitored items upfront.
   - Simulation plan and dry-run table will only show monitored items being unmonitored.
   - Prevents no-op mutations and simplifies execution logs.

---

## 4. Validation Architecture

### A. Unit Tests
1. **`tests/test_inventory_models.py`**:
   - Test `MediaInventoryItem` instantiation with `monitored=True` and `monitored=False`.
   - Test `MediaInventoryItem` default value (`monitored=True`).
   - Test `InventoryFilter` with `monitored_only` and `unmonitored_only`.
   - Test JSON round-trip serialization preserving `monitored`.
2. **`tests/test_correlator_radarr.py`**:
   - Test Radarr movie file correlation with `movie.monitored = True` and `movie.monitored = False`.
   - Test missing movie fallback.
3. **`tests/test_correlator_sonarr.py`**:
   - Test Sonarr single episode file with `episode.monitored = True` vs `False`.
   - Test Sonarr multi-episode file with all monitored, all unmonitored, and mixed monitored states.
   - Test Sonarr fallback to `series.monitored` when `episodes` list is empty.
4. **`tests/test_inventory_engine.py`**:
   - Test `filter_inventory` with `monitored_only=True` returning only monitored items.
   - Test `filter_inventory` with `unmonitored_only=True` returning only unmonitored items.
   - Test `filter_inventory` with default filter returning both.
5. **`tests/test_reporting_json.py`**:
   - Verify `"monitored": true` and `"monitored": false` in exported JSON item payloads.

### B. CLI Integration Tests
1. **`tests/test_cli_scan.py`**:
   - Test `scan --monitored` / `scan --only-monitored` / `scan --monitored-only` filters correctly.
   - Test `scan --unmonitored` / `scan --only-unmonitored` / `scan --unmonitored-only` filters correctly.
   - Test `scan --monitored --unmonitored` displays mutual exclusion error and exits with code 2.
   - Test `scan --monitored -f json` outputs JSON containing only monitored items.
2. **`tests/test_cli_clean.py`**:
   - Test `clean --unmonitor --only-monitored` only targets monitored files for unmonitoring.
   - Test `clean --delete --unmonitored` only targets unmonitored files for deletion.
   - Test `clean --monitored --unmonitored` displays mutual exclusion error and exits with code 2.

### C. Full Verification Suite
- `pytest -v` (all unit and integration tests passing)
- `ruff check .`
- `mypy src/`
