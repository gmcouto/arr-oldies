# Phase 10: Negative Language, Title, and Tag Filtering - Research Report

## 1. Executive Summary & Goals

### Objective
Enable negative audio language exclusion (`--!l` / `--not-audio-lang`), case-insensitive title substring filtering (`--title` with `ILIKE %...%` matching semantics), and named tag inclusion/exclusion (`--tag` and `--!tag`) with dynamic tag label-to-ID resolution per instance in both `scan` and `clean` commands.

### Requirements Addressed
- **INVT-07**: Exclude media files by audio language using negative language filter (`--!l`, `--not-audio-lang`, `--exclude-audio-lang`, `--not-lang`) supporting ISO-639 codes and names (e.g., `pt-br`, `por`, `portuguese`). [VERIFIED: .planning/REQUIREMENTS.md:31]
- **INVT-08**: Filter media items by case-insensitive title substring matching (`ILIKE %...%`) across movie, series, and episode titles (`--title`). [VERIFIED: .planning/REQUIREMENTS.md:32]
- **INVT-09**: Filter media items by instance tags using alphanumeric tag labels for inclusion (`--tag`) and exclusion (`--!tag` / `--exclude-tag`), dynamically resolving tag label names to tag IDs across Radarr and Sonarr instances. [VERIFIED: .planning/REQUIREMENTS.md:33]

### Key Outcomes
1. **Language Exclusion**: Users can filter out items that have specific audio tracks (e.g. `arr-oldies scan --!l pt-br` lists media that do not have Brazilian Portuguese audio).
2. **Title Substring Matching**: Users can target specific franchises or shows by partial title matching (e.g. `arr-oldies scan --title "matrix"` or `arr-oldies clean --delete --title "star wars"`).
3. **Dynamic Tag Filtering**: Users can filter by tag names/labels (e.g. `--tag 4k`, `--!tag archive`) across multiple *arr instances without manually tracking instance-specific numeric tag IDs.
4. **Command Parity**: All three filter features are uniformly supported across both `scan` and `clean` commands in both Rich table and JSON export formats.

---

## 2. Technical Architecture & Component Analysis

```
                                  CLI User Invocation
                      (--!l / --title / --tag / --!tag)
                                        │
                                        ▼
                                 Typer CLI Layer
                       (src/arr_oldies/cli.py: scan & clean)
                                        │
                   ┌────────────────────┴────────────────────┐
                   ▼                                         ▼
         MultiInstanceFetcher                        InventoryFilter
       (src/arr_oldies/api/fetcher.py)          (src/arr_oldies/inventory/models.py)
                   │                                         │
        ┌──────────┴──────────┐                              │
        ▼                     ▼                              │
  RadarrClient           SonarrClient                        │
  - GET /api/v3/tag      - GET /api/v3/tag                   │
  - GET /api/v3/movie    - GET /api/v3/series                │
  (with tags: [1, 2])    (with tags: [3, 4])                 │
        │                     │                              │
        └──────────┬──────────┘                              │
                   ▼                                         │
           HistoryCorrelator                                 │
     (src/arr_oldies/inventory/correlator.py)                │
     - Map tag IDs -> string labels                          │
     - Produces MediaInventoryItem(tags=[...])               │
                   │                                         │
                   └────────────────────┬────────────────────┘
                                        ▼
                                 InventoryEngine
                       (src/arr_oldies/inventory/engine.py)
                       - Filter 1: not_audio_langs
                       - Filter 2: title substrings
                       - Filter 3: tag inclusion/exclusion
                                        │
                                        ▼
                             Filtered Inventory Items
                         (Table / JSON / ActionExecutor)
```

### A. API Endpoints & Models (`src/arr_oldies/api/models.py` & `src/arr_oldies/constants.py`)
- **Tag API Endpoint**:
  - Radarr v3/v4: `GET /api/v3/tag` [VERIFIED: Radarr API v3 specs]
  - Sonarr v3/v4: `GET /api/v3/tag` [VERIFIED: Sonarr API v3 specs]
  - Add `RADARR_TAG_ENDPOINT = "/api/v3/tag"` and `SONARR_TAG_ENDPOINT = "/api/v3/tag"` to `src/arr_oldies/constants.py`.
- **API Models**:
  - Define `Tag(ApiBaseModel)`:
    ```python
    class Tag(ApiBaseModel):
        """Tag definition in Radarr or Sonarr."""
        id: int
        label: str
    ```
  - Update `RadarrMovie`: Add `tags: list[int] = Field(default_factory=list)`. [VERIFIED: src/arr_oldies/api/models.py:50-63]
  - Update `SonarrSeries`: Add `tags: list[int] = Field(default_factory=list)`. [VERIFIED: src/arr_oldies/api/models.py:97-107]

### B. Async Clients (`src/arr_oldies/api/radarr.py` & `src/arr_oldies/api/sonarr.py`)
- **`RadarrClient.get_tags()`**:
  ```python
  async def get_tags(self) -> list[Tag]:
      """Retrieve all tag definitions in the Radarr instance."""
      response = await self.get(RADARR_TAG_ENDPOINT)
      data = response.json()
      return [Tag.model_validate(item) for item in data]
  ```
- **`SonarrClient.get_tags()`**:
  ```python
  async def get_tags(self) -> list[Tag]:
      """Retrieve all tag definitions in the Sonarr instance."""
      response = await self.get(SONARR_TAG_ENDPOINT)
      data = response.json()
      return [Tag.model_validate(item) for item in data]
  ```
- Both methods integrate with existing error resilience and retry infrastructure in `BaseArrClient`. [VERIFIED: src/arr_oldies/api/base.py:25-95]

### C. Resilient Multi-Instance Fetcher (`src/arr_oldies/api/fetcher.py`)
- **`InstanceMediaData`**:
  - Add `tags: list[Tag] = Field(default_factory=list)`.
- **`MultiInstanceFetcher.fetch_instance_data`**:
  - In Radarr branch: concurrently retrieve tags via `client.get_tags()` alongside `client.get_movies()`.
  - In Sonarr branch: include `client.get_tags()` in the `asyncio.gather(...)` call.
  - Graceful fallback: If an instance does not support tags or fails retrieving `/api/v3/tag`, default to `tags=[]` so media library scanning succeeds without crashing. [VERIFIED: src/arr_oldies/api/fetcher.py:73-120]

### D. History Correlator & Dynamic Tag Resolution (`src/arr_oldies/inventory/correlator.py`)
- **Tag Label Mapping**:
  - In `HistoryCorrelator._correlate_radarr`:
    - Construct `tags_by_id: dict[int, str] = {t.id: t.label for t in instance_data.tags}`.
    - For each movie: `movie_tags = [tags_by_id[tid] for tid in movie.tags if tid in tags_by_id] if movie and movie.tags else []`.
    - Pass `tags=movie_tags` to `MediaInventoryItem`.
  - In `HistoryCorrelator._correlate_sonarr`:
    - Construct `tags_by_id: dict[int, str] = {t.id: t.label for t in instance_data.tags}`.
    - For each episode file: `series_tags = [tags_by_id[tid] for tid in series.tags if tid in tags_by_id] if series and series.tags else []`.
    - Pass `tags=series_tags` to `MediaInventoryItem`.
  - Result: `MediaInventoryItem.tags` holds human-readable tag labels (e.g. `["4k", "archive"]`) rather than instance-specific integer IDs. [VERIFIED: src/arr_oldies/inventory/correlator.py:136-248, 250-423]

### E. Inventory Data Models (`src/arr_oldies/inventory/models.py`)
- **`MediaInventoryItem`**:
  - Add `tags: list[str] = Field(default_factory=list, description="Resolved tag labels assigned to media item")`.
  - Backward compatible: Defaults to `[]`.
- **`InventoryFilter`**:
  - Add:
    ```python
    not_audio_langs: list[str] | None = None
    titles: list[str] | None = None
    tags: list[str] | None = None
    not_tags: list[str] | None = None
    ```
  [VERIFIED: src/arr_oldies/inventory/models.py:44-110]

### F. Inventory Engine Filtering Logic (`src/arr_oldies/inventory/engine.py`)
- **Negative Audio Language Filter (`INVT-07`)**:
  - Uses `LanguageNormalizer.matches(item.audio_languages, query)`.
  ```python
  if criteria.not_audio_langs and any(
      self.normalizer.matches(item.audio_languages, q) for q in criteria.not_audio_langs
  ):
      continue
  ```
- **Title Substring Filter (`INVT-08`)**:
  - Matches case-insensitively across `item.title` (movie/series title) and `item.episode_title` (episode title).
  ```python
  if criteria.titles:
      matched_title = False
      for q in criteria.titles:
          clean_q = q.strip().lower()
          if not clean_q:
              continue
          if clean_q in item.title.lower() or (
              item.episode_title and clean_q in item.episode_title.lower()
          ):
              matched_title = True
              break
      if not matched_title:
          continue
  ```
- **Tag Inclusion Filter (`INVT-09`)**:
  - Checks if item has any of the requested tag labels (case-insensitive).
  ```python
  if criteria.tags:
      item_tags = {t.strip().lower() for t in item.tags}
      if not any(q.strip().lower() in item_tags for q in criteria.tags if q.strip()):
          continue
  ```
- **Tag Exclusion Filter (`INVT-09`)**:
  - Checks if item has any of the excluded tag labels (case-insensitive).
  ```python
  if criteria.not_tags:
      item_tags = {t.strip().lower() for t in item.tags}
      if any(q.strip().lower() in item_tags for q in criteria.not_tags if q.strip()):
          continue
  ```
  [VERIFIED: src/arr_oldies/inventory/engine.py:23-101]

### G. Typer CLI Options (`src/arr_oldies/cli.py`)
Add identical options to both `scan_command` and `clean_command`:
```python
not_audio_lang: Annotated[
    list[str] | None,
    typer.Option(
        "--!l",
        "--not-audio-lang",
        "--exclude-audio-lang",
        "--not-lang",
        help="Exclude media items containing specified audio language (repeatable, e.g. --!l pt-br).",
    ),
] = None,
title: Annotated[
    list[str] | None,
    typer.Option(
        "--title",
        help="Filter by case-insensitive title substring matching across movie, series, and episode titles (repeatable).",
    ),
] = None,
tag: Annotated[
    list[str] | None,
    typer.Option(
        "--tag",
        help="Filter media items having the specified tag label (repeatable, e.g. --tag 4k).",
    ),
] = None,
not_tag: Annotated[
    list[str] | None,
    typer.Option(
        "--!tag",
        "--exclude-tag",
        "--not-tag",
        help="Exclude media items having the specified tag label (repeatable, e.g. --!tag archive).",
    ),
] = None,
```
CLI parses and binds these options into `InventoryFilter`:
```python
criteria = InventoryFilter(
    media_types=[media_type] if media_type else None,
    audio_langs=audio_lang,
    not_audio_langs=not_audio_lang,
    titles=title,
    tags=tag,
    not_tags=not_tag,
    min_size_bytes=min_size_bytes,
    max_size_bytes=max_size_bytes,
    min_age_days=min_age_days,
    max_age_days=max_age_days,
    before_date=before_date,
    after_date=after_date,
    legacy_only=legacy,
    history_only=history,
    monitored_only=monitored,
    unmonitored_only=unmonitored,
)
```
[VERIFIED: src/arr_oldies/cli.py:210-377, 526-704]

### H. JSON Export & Table Rendering (`src/arr_oldies/reporting/`)
- `json_export.py`: `item.model_dump(mode="json")` automatically outputs `"tags": ["4k", "archive"]`. [VERIFIED: src/arr_oldies/reporting/json_export.py:61-65]
- `formatters.py` / `table.py`: Items display cleanly in the terminal, preserving table formatting and markup escaping.

---

## 3. Pitfalls & Edge Cases

| Edge Case | Description | Mitigation Strategy |
|-----------|-------------|---------------------|
| **Exclamation Mark in Flag Names** | Typer / Click parsing `--!l` and `--!tag`. | Tested and verified directly in virtual environment: Typer parses `--!l` and `--!tag` without syntax errors. All standard aliases (`--not-audio-lang`, `--exclude-tag`, etc.) are also registered. [VERIFIED: Typer CLI test] |
| **Instance-Specific Tag IDs** | Instance A has tag "4k" (ID 1) while Instance B has tag "4k" (ID 5). Direct ID matching across instances would fail or cross-contaminate. | Tag IDs are resolved dynamically to string labels at the instance fetch/correlation boundary. Filtering operates entirely on normalized string labels. [VERIFIED: Architecture analysis] |
| **Missing / Unset Tags** | Movies or series with no tags assigned (`tags=[]` or `tags=None` in API response). | Default `tags` to `[]` in models. Tag inclusion filter (`--tag 4k`) skips items with empty tags; tag exclusion filter (`--!tag archive`) keeps items with empty tags. |
| **Multi-Language Audio Tracks** | Media file containing both English and Portuguese tracks (`["English", "Portuguese"]`). | If user passes `--!l pt-br`, `LanguageNormalizer.matches` evaluates to `True`, correctly excluding the item. If user passes `-l en --!l pt-br`, item is excluded because it violates the negative constraint. |
| **Case & Whitespace Normalization** | User passes `--title "  matrix  "` or `--tag "4K"` or `--tag "  uhd  "`. | All filter predicates strip whitespace and normalize strings to lowercase before checking containment. |
| **Multi-Episode Files & Episode Titles** | Sonarr episode files covering multiple episodes (`[S01E01, S01E02]`). | Title matching checks `item.title` (series title) and `item.episode_title` (first episode title). Substring matches anywhere in either field trigger inclusion. |
| **Tag Fetch API Failure** | One *arr instance fails `/api/v3/tag` due to permission or version limitation. | Multi-instance fetcher catches tag fetch errors gracefully and falls back to empty tags list without failing the entire instance scan. [VERIFIED: API-04 resilience pattern] |

---

## 4. Stack, Patterns, & Claim Provenance

### Standard Stack & Versions
- **Python**: 3.12+ [VERIFIED: pyproject.toml:13]
- **Typer**: >=0.12.0 [VERIFIED: pyproject.toml:16]
- **Pydantic**: >=2.7.0 [VERIFIED: pyproject.toml:18]
- **HTTPX**: >=0.27.0 [VERIFIED: pyproject.toml:17]
- **Rich**: >=13.7.0 [VERIFIED: pyproject.toml:19]
- **pytest & respx**: pytest-9.1.1, respx-0.23.1 [VERIFIED: .venv pytest session]

### Pattern Provenance
1. **Composable In-Memory Filtering**: Following the single-pass filtering pattern in `src/arr_oldies/inventory/engine.py:51-100`.
2. **Dynamic Tag Label Resolution**: Resolving integer foreign keys to string descriptors at the correlator layer, isolating instance-specific database ID differences from unified inventory representations (`src/arr_oldies/inventory/correlator.py`).
3. **Safe Action Mutation Pipeline**: Filtering criteria cleanly propagate through `scan` and `clean` into `ActionPlan` generation (`src/arr_oldies/cli.py:738-745`).

---

## 5. Validation & Test Plan

### A. Unit Tests
1. **`tests/test_api_models.py` & `tests/test_radarr_client.py` / `tests/test_sonarr_client.py`**:
   - Verify `Tag` model validation (`id`, `label`).
   - Verify `RadarrMovie.tags` and `SonarrSeries.tags` deserialization.
   - Verify `RadarrClient.get_tags()` and `SonarrClient.get_tags()` endpoint calls against mocked `/api/v3/tag`.
2. **`tests/test_correlator_radarr.py` & `tests/test_correlator_sonarr.py`**:
   - Verify `HistoryCorrelator` maps `movie.tags = [1, 2]` to `item.tags = ["4k", "archive"]`.
   - Verify Sonarr series tags are propagated to episode inventory items.
   - Verify handling when tag ID is missing in tag map or tags list is empty.
3. **`tests/test_inventory_models.py`**:
   - Verify `MediaInventoryItem` instantiation with `tags`.
   - Verify `InventoryFilter` instantiation with `not_audio_langs`, `titles`, `tags`, `not_tags`.
4. **`tests/test_inventory_engine.py`**:
   - Test negative audio language filter (`not_audio_langs=["pt-br"]`, `not_audio_langs=["por"]`, `not_audio_langs=["portuguese"]`).
   - Test title substring filter (`titles=["matrix"]`, `titles=["drama"]`, `titles=["ozymandias"]`).
   - Test tag inclusion filter (`tags=["4k"]`).
   - Test tag exclusion filter (`not_tags=["archive"]`).
   - Test combined filters (e.g. `audio_langs=["en"]`, `not_audio_langs=["pt-br"]`, `titles=["movie"]`, `tags=["4k"]`, `not_tags=["archive"]`).

### B. Integration Tests (`tests/test_cli_scan.py` & `tests/test_cli_clean.py`)
1. **`test_cli_scan.py`**:
   - Test `scan --!l pt-br` and `--not-audio-lang pt-br` excludes Portuguese items.
   - Test `scan --title matrix` filters to items containing "matrix" case-insensitively.
   - Test `scan --tag 4k` and `scan --!tag archive` in table mode and `--format json`.
2. **`test_cli_clean.py`**:
   - Test `clean --delete --!l pt-br` only plans deletion for non-Portuguese items.
   - Test `clean --unmonitor --title "breaking"` only plans unmonitor for matching series.
   - Test `clean --delete --tag 4k --!tag archive --execute --yes` executes deletion on filtered items.

### C. Full Verification Suite
- `pytest -v` (all unit and integration tests passing)
- `ruff check .`
- `mypy src/`

---

## 6. Implementation Breakdown & Wave Recommendations

The work for Phase 10 is cohesive and can be executed across two structured waves or a single comprehensive plan:

- **Wave 1: Core API Models, Clients, Tag Fetching & Dynamic Correlator Resolution**
  - Add `Tag` model, `RADARR_TAG_ENDPOINT`, `SONARR_TAG_ENDPOINT`.
  - Add `get_tags()` to `RadarrClient` and `SonarrClient`.
  - Update `MultiInstanceFetcher` to retrieve tags.
  - Update `HistoryCorrelator` to map tag IDs to tag labels on `MediaInventoryItem`.
  - Unit tests for clients, fetcher, and correlator.

- **Wave 2: Inventory Engine Filters, Typer CLI Integration & Test Suite**
  - Add `not_audio_langs`, `titles`, `tags`, `not_tags` to `InventoryFilter`.
  - Implement negative language, title substring, and tag inclusion/exclusion in `InventoryEngine.filter_inventory`.
  - Add CLI flags and aliases to `scan_command` and `clean_command` in `cli.py`.
  - Update `README.md` documentation to document `--!l`, `--title`, `--tag`, and `--!tag`.
  - Comprehensive unit and integration test suite across `test_inventory_engine.py`, `test_cli_scan.py`, and `test_cli_clean.py`.
