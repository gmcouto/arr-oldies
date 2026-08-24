# Phase 03: Media Inventory & History Timestamp Correlator — Pattern Map

**Mapped:** 2026-08-23  
**Files analyzed:** 15 (7 source files, 8 test files/extensions)  
**Analogs found:** 15 / 15 (100% matched)  

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `src/arr_oldies/inventory/__init__.py` | config / utility | transform | `src/arr_oldies/api/__init__.py` | exact |
| `src/arr_oldies/inventory/models.py` | model | transform | `src/arr_oldies/api/models.py` | exact |
| `src/arr_oldies/inventory/languages.py` | utility / service | transform | `src/arr_oldies/targeting.py` | role-match |
| `src/arr_oldies/inventory/parser.py` | utility | transform | `src/arr_oldies/config.py` | role-match |
| `src/arr_oldies/inventory/correlator.py` | service | batch / transform | `src/arr_oldies/api/fetcher.py` | role-match |
| `src/arr_oldies/inventory/engine.py` | service / controller | batch / transform | `src/arr_oldies/targeting.py` | role-match |
| `src/arr_oldies/exceptions.py` (extend) | model / utility | request-response | `src/arr_oldies/exceptions.py` | exact |
| `src/arr_oldies/constants.py` (extend) | config / utility | request-response | `src/arr_oldies/constants.py` | exact |
| `tests/test_language_normalizer.py` | test | transform | `tests/test_api_models.py` | exact |
| `tests/test_parser.py` | test | transform | `tests/test_config.py` | exact |
| `tests/test_inventory_models.py` | test | transform | `tests/test_api_models.py` | exact |
| `tests/test_correlator_radarr.py` | test | batch / transform | `tests/test_history_fetcher.py` | role-match |
| `tests/test_correlator_sonarr.py` | test | batch / transform | `tests/test_history_fetcher.py` | role-match |
| `tests/test_correlator_legacy.py` | test | batch / transform | `tests/test_history_fetcher.py` | role-match |
| `tests/test_inventory_engine.py` | test | batch / transform | `tests/test_targeting.py` | role-match |

---

## Pattern Assignments

### 1. `src/arr_oldies/inventory/__init__.py` (config / utility, transform)

**Analog:** `src/arr_oldies/api/__init__.py`

**Imports and Module Re-Exports Pattern** (derived from `src/arr_oldies/api/__init__.py:1-48`):
```python
"""Media inventory indexing, History API correlation, and filtering engine."""

from arr_oldies.inventory.correlator import (
    HistoryCorrelator,
    RadarrHistoryIndex,
    SonarrHistoryIndex,
)
from arr_oldies.inventory.engine import InventoryEngine
from arr_oldies.inventory.languages import LanguageEntry, LanguageNormalizer
from arr_oldies.inventory.models import (
    HistoryStatus,
    InventoryFilter,
    InventorySummary,
    MediaInventoryItem,
    MediaType,
    SortDirection,
    SortKey,
)
from arr_oldies.inventory.parser import parse_age_cutoff, parse_date_cutoff, parse_size

__all__ = [
    "HistoryCorrelator",
    "HistoryStatus",
    "InventoryEngine",
    "InventoryFilter",
    "InventorySummary",
    "LanguageEntry",
    "LanguageNormalizer",
    "MediaInventoryItem",
    "MediaType",
    "RadarrHistoryIndex",
    "SonarrHistoryIndex",
    "SortDirection",
    "SortKey",
    "parse_age_cutoff",
    "parse_date_cutoff",
    "parse_size",
]
```

---

### 2. `src/arr_oldies/inventory/models.py` (model, transform)

**Analog:** `src/arr_oldies/api/models.py:1-13` and `src/arr_oldies/models.py:1-13`

**Enum and Schema Pattern** (derived from `src/arr_oldies/models.py:8-13` and `src/arr_oldies/api/models.py:9-31`):
```python
"""Pydantic v2 data models for unified media inventory, filter options, and summaries."""

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from arr_oldies.models import InstanceType


class MediaType(StrEnum):
    """Media item classification."""

    MOVIE = "movie"
    EPISODE = "episode"


class HistoryStatus(StrEnum):
    """History correlation status."""

    IMPORTED = "imported"
    GRABBED_AND_IMPORTED = "grabbed_and_imported"
    LEGACY = "legacy"
    UNINDEXED = "unindexed"


class SortKey(StrEnum):
    """Inventory sort ordering key."""

    IMPORT_DATE = "import_date"
    GRAB_DATE = "grab_date"
    SIZE = "size"
    TITLE = "title"
    AGE = "age"


class SortDirection(StrEnum):
    """Sort direction."""

    ASC = "asc"
    DESC = "desc"


class MediaInventoryItem(BaseModel):
    """Unified inventory record combining Radarr movies and Sonarr TV episodes."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    id: str = Field(description="Unique inventory item identifier (e.g. radarr:101 or sonarr:201)")
    instance_name: str
    instance_type: InstanceType
    media_type: MediaType
    title: str
    year: int | None = None
    season_number: int | None = None
    episode_numbers: list[int] = Field(default_factory=list)
    formatted_episode: str | None = None
    episode_title: str | None = None
    movie_id: int | None = None
    movie_file_id: int | None = None
    series_id: int | None = None
    episode_file_id: int | None = None
    episode_ids: list[int] = Field(default_factory=list)
    file_path: str
    relative_path: str = ""
    size_bytes: int = 0
    audio_languages: list[str] = Field(default_factory=list)
    raw_audio_languages: str | None = None
    video_codec: str | None = None
    resolution: str | None = None
    import_date: datetime
    grab_date: datetime | None = None
    age_days: int = 0
    has_history: bool = True
    is_legacy: bool = False
    history_status: HistoryStatus = HistoryStatus.IMPORTED
    source_title: str | None = None
    download_id: str | None = None

    @field_validator("import_date", "grab_date", mode="after")
    @classmethod
    def ensure_utc(cls, v: datetime | None) -> datetime | None:
        """Ensure all stored datetimes are timezone-aware in UTC."""
        if v is None:
            return None
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v.astimezone(timezone.utc)


class InventoryFilter(BaseModel):
    """Filter criteria applied to in-memory media inventory."""

    model_config = ConfigDict(extra="ignore")

    media_types: list[MediaType] | None = None
    instance_names: list[str] | None = None
    audio_langs: list[str] | None = None
    min_size_bytes: int | None = None
    max_size_bytes: int | None = None
    min_age_days: int | None = None
    max_age_days: int | None = None
    before_date: datetime | None = None
    after_date: datetime | None = None
    legacy_only: bool = False
    history_only: bool = False


class InventorySummary(BaseModel):
    """Aggregated statistical metrics across an inventory collection."""

    model_config = ConfigDict(extra="ignore")

    total_items: int = 0
    total_size_bytes: int = 0
    movie_count: int = 0
    episode_count: int = 0
    legacy_count: int = 0
    oldest_import_date: datetime | None = None
    newest_import_date: datetime | None = None
    oldest_grab_date: datetime | None = None
    instances_breakdown: dict[str, int] = Field(default_factory=dict)
```

---

### 3. `src/arr_oldies/inventory/languages.py` (utility / service, transform)

**Analog:** `src/arr_oldies/targeting.py:29-48` and `src/arr_oldies/api/models.py:15-31`

**Normalization and Matching Pattern** (derived from `src/arr_oldies/targeting.py` normalization dictionaries):
```python
"""Audio language extraction, ISO-639 normalization, and synonym matching."""

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class LanguageEntry:
    """Canonical ISO-639 language specification and lookup aliases."""

    code_2: str | None  # e.g., "en", "ja", "fr"
    code_3: str  # e.g., "eng", "jpn", "fre"/"fra"
    name: str  # e.g., "English", "Japanese", "French"
    synonyms: tuple[str, ...] = ()


# Regex splitting common audio language delimiters: '/', ',', '+', '|', ';', '\'
LANGUAGE_DELIMITERS_REGEX = re.compile(r"[/,+\|;\\]+")


class LanguageNormalizer:
    """Canonical ISO-639 language resolver with bidirectional lookup."""

    def __init__(self) -> None:
        self._lookup: dict[str, LanguageEntry] = {}
        self._build_table()

    def _build_table(self) -> None:
        """Register ISO-639 standard mappings and common synonyms."""
        entries: list[LanguageEntry] = [
            LanguageEntry("en", "eng", "English", ("en-us", "en-gb")),
            LanguageEntry("ja", "jpn", "Japanese", ("jap", "nihongo")),
            LanguageEntry("fr", "fre", "French", ("fra", "francais")),
            LanguageEntry("de", "ger", "German", ("deu", "deutsch")),
            LanguageEntry("es", "spa", "Spanish", ("espanol", "castilian")),
            LanguageEntry("it", "ita", "Italian", ("italiano",)),
            LanguageEntry("ko", "kor", "Korean", ("korean",)),
            LanguageEntry("zh", "chi", "Chinese", ("zho", "mandarin", "cantonese")),
            LanguageEntry("ru", "rus", "Russian", ("russkiy",)),
            LanguageEntry("pt", "por", "Portuguese", ("portugues", "pt-br")),
            LanguageEntry("hi", "hin", "Hindi", ()),
            LanguageEntry("ar", "ara", "Arabic", ()),
            LanguageEntry(None, "und", "Undetermined", ("unknown", "undetermined")),
        ]
        for entry in entries:
            self._register_entry(entry)

    def _register_entry(self, entry: LanguageEntry) -> None:
        if entry.code_2:
            self._lookup[entry.code_2.lower()] = entry
        self._lookup[entry.code_3.lower()] = entry
        self._lookup[entry.name.lower()] = entry
        for syn in entry.synonyms:
            self._lookup[syn.lower()] = entry

    def extract_languages(self, raw_audio_languages: str | None) -> list[str]:
        """Extract, split, and normalize audio languages from mediaInfo string."""
        if not raw_audio_languages or not raw_audio_languages.strip():
            return []

        tokens = LANGUAGE_DELIMITERS_REGEX.split(raw_audio_languages.strip())
        results: list[str] = []
        seen: set[str] = set()

        for token in tokens:
            clean = token.strip().strip("[]()").lower()
            if not clean:
                continue
            entry = self._lookup.get(clean)
            canonical = entry.name if entry else token.strip()
            if canonical.lower() not in seen:
                seen.add(canonical.lower())
                results.append(canonical)

        return results

    def matches(self, item_languages: list[str], target_query: str) -> bool:
        """Check if any item language matches the user query (by code or name)."""
        clean_target = target_query.strip().lower()
        target_entry = self._lookup.get(clean_target)

        target_identifiers: set[str] = {clean_target}
        if target_entry:
            if target_entry.code_2:
                target_identifiers.add(target_entry.code_2.lower())
            target_identifiers.add(target_entry.code_3.lower())
            target_identifiers.add(target_entry.name.lower())
            target_identifiers.update(s.lower() for s in target_entry.synonyms)

        for lang in item_languages:
            clean_lang = lang.strip().lower()
            if clean_lang in target_identifiers:
                return True
            entry = self._lookup.get(clean_lang)
            if entry:
                if (
                    entry.name.lower() in target_identifiers
                    or entry.code_3.lower() in target_identifiers
                    or (entry.code_2 and entry.code_2.lower() in target_identifiers)
                ):
                    return True

        return False
```

---

### 4. `src/arr_oldies/inventory/parser.py` (utility, transform)

**Analog:** `src/arr_oldies/config.py:18-39` and `src/arr_oldies/exceptions.py:4-10`

**String Parsing and Domain Error Handling Pattern**:
```python
"""Human-friendly string parsing for file sizes, age intervals, and date cutoffs."""

import re
from datetime import datetime, timezone

from arr_oldies.exceptions import ParseError

SIZE_REGEX = re.compile(r"^\s*([0-9]+(?:\.[0-9]+)?)\s*([a-zA-Z]*)\s*$")
AGE_REGEX = re.compile(r"^\s*([0-9]+)\s*([a-zA-Z]*)\s*$")

SIZE_MULTIPLIERS: dict[str, int] = {
    "": 1,
    "b": 1,
    "k": 1024,
    "kb": 1000,
    "kib": 1024,
    "m": 1024**2,
    "mb": 1000**2,
    "mib": 1024**2,
    "g": 1024**3,
    "gb": 1000**3,
    "gib": 1024**3,
    "t": 1024**4,
    "tb": 1000**4,
    "tib": 1024**4,
}


def parse_size(size_str: str) -> int:
    """Parse human size string (e.g., '500MB', '2GB', '1.5GiB', '100M') into integer bytes."""
    match = SIZE_REGEX.match(size_str)
    if not match:
        raise ParseError(
            f"Invalid size specification: '{size_str}'. Examples: '500MB', '2GB', '1.5GiB'."
        )

    val_str, unit_raw = match.groups()
    unit = unit_raw.lower()

    multiplier = SIZE_MULTIPLIERS.get(unit)
    if multiplier is None:
        raise ParseError(
            f"Unknown size unit '{unit_raw}' in '{size_str}'. Supported: B, KB, KiB, MB, MiB, GB, GiB, TB, TiB."
        )

    return int(float(val_str) * multiplier)


def parse_age_cutoff(age_str: str) -> int:
    """Parse human age interval (e.g., '30d', '6m', '1y', '2w', '90') into integer days."""
    match = AGE_REGEX.match(age_str)
    if not match:
        raise ParseError(
            f"Invalid age specification: '{age_str}'. Examples: '30d', '6m', '1y', '2w'."
        )

    val_str, unit_raw = match.groups()
    val = int(val_str)
    unit = unit_raw.lower()

    if unit in ("", "d", "day", "days"):
        return val
    elif unit in ("w", "week", "weeks"):
        return val * 7
    elif unit in ("m", "month", "months", "mo"):
        return val * 30
    elif unit in ("y", "year", "years", "yr"):
        return val * 365
    else:
        raise ParseError(
            f"Unknown age unit '{unit_raw}' in '{age_str}'. Supported units: d (days), w (weeks), m (months), y (years)."
        )


def parse_date_cutoff(date_str: str) -> datetime:
    """Parse ISO-8601 or YYYY-MM-DD date string into UTC datetime."""
    clean = date_str.strip()
    try:
        if "T" in clean:
            dt = datetime.fromisoformat(clean.replace("Z", "+00:00"))
        else:
            dt = datetime.strptime(clean, "%Y-%m-%d")
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except ValueError as exc:
        raise ParseError(
            f"Invalid date format: '{date_str}'. Expected 'YYYY-MM-DD' or ISO-8601 format."
        ) from exc
```

---

### 5. `src/arr_oldies/inventory/correlator.py` (service, batch / transform)

**Analog:** `src/arr_oldies/api/fetcher.py:25-50` and `src/arr_oldies/api/models.py:65-75`

**History Event Indexing and Timestamp Correlation Pattern**:
```python
"""History API timestamp correlation engine for Radarr and Sonarr libraries."""

from collections import defaultdict
from datetime import datetime, timezone

from arr_oldies.api.fetcher import InstanceMediaData
from arr_oldies.api.models import (
    RadarrHistoryRecord,
    RadarrMovie,
    RadarrMovieFile,
    SonarrEpisode,
    SonarrEpisodeFile,
    SonarrHistoryRecord,
    SonarrSeries,
)
from arr_oldies.inventory.languages import LanguageNormalizer
from arr_oldies.inventory.models import HistoryStatus, MediaInventoryItem, MediaType
from arr_oldies.models import InstanceType


class RadarrHistoryIndex:
    """In-memory multi-key hash index for Radarr history records."""

    def __init__(self, records: list[RadarrHistoryRecord]) -> None:
        self.imports_by_file_id: dict[int, list[RadarrHistoryRecord]] = defaultdict(list)
        self.imports_by_path: dict[str, list[RadarrHistoryRecord]] = defaultdict(list)
        self.imports_by_movie_id: dict[int, list[RadarrHistoryRecord]] = defaultdict(list)
        self.grabs_by_download_id: dict[str, RadarrHistoryRecord] = {}
        self.grabs_by_movie_id: dict[int, list[RadarrHistoryRecord]] = defaultdict(list)

        for record in records:
            event_type = record.event_type.lower()
            if event_type in ("downloadfolderimported", "moviefileimported", "imported", "3"):
                file_id_raw = record.data.get("fileId") or record.data.get("movieFileId")
                if file_id_raw is not None:
                    try:
                        self.imports_by_file_id[int(file_id_raw)].append(record)
                    except (ValueError, TypeError):
                        pass

                imported_path = record.data.get("importedPath") or record.data.get("path")
                if imported_path:
                    self.imports_by_path[imported_path.lower()].append(record)

                self.imports_by_movie_id[record.movie_id].append(record)

            elif event_type in ("grabbed", "1"):
                if record.download_id:
                    self.grabs_by_download_id[record.download_id] = record
                self.grabs_by_movie_id[record.movie_id].append(record)


class SonarrHistoryIndex:
    """In-memory multi-key hash index for Sonarr history records."""

    def __init__(self, records: list[SonarrHistoryRecord]) -> None:
        self.imports_by_file_id: dict[int, list[SonarrHistoryRecord]] = defaultdict(list)
        self.imports_by_episode_id: dict[int, list[SonarrHistoryRecord]] = defaultdict(list)
        self.imports_by_path: dict[str, list[SonarrHistoryRecord]] = defaultdict(list)
        self.grabs_by_download_id: dict[str, SonarrHistoryRecord] = {}
        self.grabs_by_episode_id: dict[int, list[SonarrHistoryRecord]] = defaultdict(list)
        self.grabs_by_series_id: dict[int, list[SonarrHistoryRecord]] = defaultdict(list)

        for record in records:
            event_type = record.event_type.lower()
            if event_type in ("downloadfolderimported", "episodefileimported", "imported", "3"):
                file_id_raw = record.data.get("fileId") or record.data.get("episodeFileId")
                if file_id_raw is not None:
                    try:
                        self.imports_by_file_id[int(file_id_raw)].append(record)
                    except (ValueError, TypeError):
                        pass

                imported_path = record.data.get("importedPath") or record.data.get("path")
                if imported_path:
                    self.imports_by_path[imported_path.lower()].append(record)

                if record.episode_id:
                    self.imports_by_episode_id[record.episode_id].append(record)

            elif event_type in ("grabbed", "1"):
                if record.download_id:
                    self.grabs_by_download_id[record.download_id] = record
                if record.episode_id:
                    self.grabs_by_episode_id[record.episode_id].append(record)
                self.grabs_by_series_id[record.series_id].append(record)


class HistoryCorrelator:
    """Correlates media files with History API events and standardizes inventory items."""

    def __init__(self, normalizer: LanguageNormalizer | None = None) -> None:
        self.normalizer = normalizer or LanguageNormalizer()

    def correlate_instance(
        self,
        instance_data: InstanceMediaData,
        reference_time: datetime | None = None,
    ) -> list[MediaInventoryItem]:
        """Correlate all media files from an instance into MediaInventoryItem records."""
        now_utc = reference_time or datetime.now(timezone.utc)

        if instance_data.instance_type == InstanceType.RADARR:
            return self._correlate_radarr(instance_data, now_utc)
        elif instance_data.instance_type == InstanceType.SONARR:
            return self._correlate_sonarr(instance_data, now_utc)
        else:
            raise ValueError(f"Unsupported instance type: '{instance_data.instance_type}'")
```

---

### 6. `src/arr_oldies/inventory/engine.py` (service / controller, batch / transform)

**Analog:** `src/arr_oldies/targeting.py:7-72` and `src/arr_oldies/api/fetcher.py:137-175`

**Composable Filtering, Sorting, and Summary Metrics Pattern**:
```python
"""Inventory processing engine: composable filtering, deterministic sorting, and metrics generation."""

from datetime import datetime, timezone
from typing import Any

from arr_oldies.inventory.languages import LanguageNormalizer
from arr_oldies.inventory.models import (
    InventoryFilter,
    InventorySummary,
    MediaInventoryItem,
    SortDirection,
    SortKey,
)


class InventoryEngine:
    """Orchestrates inventory filtering, sorting, and aggregate summary generation."""

    def __init__(self, normalizer: LanguageNormalizer | None = None) -> None:
        self.normalizer = normalizer or LanguageNormalizer()

    def filter_inventory(
        self,
        items: list[MediaInventoryItem],
        criteria: InventoryFilter,
    ) -> list[MediaInventoryItem]:
        """Filter media inventory items matching all specified criteria."""
        filtered: list[MediaInventoryItem] = []

        for item in items:
            # 1. Media Type Filter
            if criteria.media_types and item.media_type not in criteria.media_types:
                continue

            # 2. Instance Filter
            if criteria.instance_names:
                norm_instances = {n.lower() for n in criteria.instance_names}
                if item.instance_name.lower() not in norm_instances:
                    continue

            # 3. Size Bounds Filter (bytes)
            if criteria.min_size_bytes is not None and item.size_bytes < criteria.min_size_bytes:
                continue
            if criteria.max_size_bytes is not None and item.size_bytes > criteria.max_size_bytes:
                continue

            # 4. Age Bounds Filter (days)
            if criteria.min_age_days is not None and item.age_days < criteria.min_age_days:
                continue
            if criteria.max_age_days is not None and item.age_days > criteria.max_age_days:
                continue

            # 5. Date Bounds Filter
            if criteria.before_date is not None and item.import_date >= criteria.before_date:
                continue
            if criteria.after_date is not None and item.import_date <= criteria.after_date:
                continue

            # 6. Legacy / History Filter
            if criteria.legacy_only and item.has_history:
                continue
            if criteria.history_only and not item.has_history:
                continue

            # 7. Audio Language Filter
            if criteria.audio_langs:
                if not any(
                    self.normalizer.matches(item.audio_languages, q) for q in criteria.audio_langs
                ):
                    continue

            filtered.append(item)

        return filtered

    def sort_inventory(
        self,
        items: list[MediaInventoryItem],
        sort_key: SortKey = SortKey.IMPORT_DATE,
        direction: SortDirection = SortDirection.ASC,
    ) -> list[MediaInventoryItem]:
        """Sort inventory items deterministically with stable tie-breaking."""
        reverse = direction == SortDirection.DESC

        def _sort_extractor(item: MediaInventoryItem) -> tuple[Any, ...]:
            if sort_key == SortKey.IMPORT_DATE:
                return (item.import_date, item.title.lower(), item.id)
            elif sort_key == SortKey.GRAB_DATE:
                # Fallback to import_date if grab_date is None
                return (item.grab_date or item.import_date, item.title.lower(), item.id)
            elif sort_key == SortKey.SIZE:
                return (item.size_bytes, item.import_date, item.title.lower(), item.id)
            elif sort_key == SortKey.TITLE:
                return (item.title.lower(), item.import_date, item.id)
            elif sort_key == SortKey.AGE:
                return (item.age_days, item.title.lower(), item.id)
            return (item.import_date, item.title.lower(), item.id)

        return sorted(items, key=_sort_extractor, reverse=reverse)

    def generate_summary(self, items: list[MediaInventoryItem]) -> InventorySummary:
        """Compute aggregate summary metrics across inventory items."""
        if not items:
            return InventorySummary()

        total_size = sum(item.size_bytes for item in items)
        movies = sum(1 for item in items if item.media_type == "movie")
        episodes = sum(1 for item in items if item.media_type == "episode")
        legacy = sum(1 for item in items if item.is_legacy)

        import_dates = [item.import_date for item in items]
        grab_dates = [item.grab_date for item in items if item.grab_date is not None]

        instances_breakdown: dict[str, int] = {}
        for item in items:
            instances_breakdown[item.instance_name] = (
                instances_breakdown.get(item.instance_name, 0) + 1
            )

        return InventorySummary(
            total_items=len(items),
            total_size_bytes=total_size,
            movie_count=movies,
            episode_count=episodes,
            legacy_count=legacy,
            oldest_import_date=min(import_dates) if import_dates else None,
            newest_import_date=max(import_dates) if import_dates else None,
            oldest_grab_date=min(grab_dates) if grab_dates else None,
            instances_breakdown=instances_breakdown,
        )
```

---

### 7. `src/arr_oldies/exceptions.py` (model / utility, request-response)

**Analog:** `src/arr_oldies/exceptions.py:1-40`

**Exception Hierarchy Extension Pattern** (derived from `src/arr_oldies/exceptions.py:1-75`):
```python
# Inventory and parsing domain exceptions (per INVT-01..06)
class InventoryError(ArrOldiesError):
    """Base exception for inventory correlation and processing errors."""


class ParseError(ArrOldiesError):
    """Raised when parsing human size, age, or date filter strings fails."""


class CorrelationError(InventoryError):
    """Raised when critical media metadata or history correlation fails."""
```

---

### 8. `src/arr_oldies/constants.py` (config / utility, request-response)

**Analog:** `src/arr_oldies/constants.py:1-55`

**Constants Extension Pattern** (derived from `src/arr_oldies/constants.py:1-39`):
```python
# Inventory defaults (per INVT-04, INVT-05)
DEFAULT_SORT_KEY: str = "import_date"
DEFAULT_SORT_DIRECTION: str = "asc"
```

---

## Test Pattern Assignments

### 9. `tests/test_language_normalizer.py` (test, transform)

**Analog:** `tests/test_api_models.py:22-55`

**Test Pattern**:
```python
"""Unit tests for LanguageNormalizer audio language extraction, ISO-639 normalization, and matching."""

import pytest

from arr_oldies.inventory.languages import LanguageNormalizer


@pytest.fixture
def normalizer() -> LanguageNormalizer:
    return LanguageNormalizer()


def test_extract_languages_simple(normalizer: LanguageNormalizer):
    """Verify single language string extraction."""
    langs = normalizer.extract_languages("eng")
    assert langs == ["English"]


def test_extract_languages_compound_delimiters(normalizer: LanguageNormalizer):
    """Verify extraction across varied delimiters: '/', ',', '+', '|'."""
    assert normalizer.extract_languages("eng/fre") == ["English", "French"]
    assert normalizer.extract_languages("Japanese, English") == ["Japanese", "English"]
    assert normalizer.extract_languages("deu+ita") == ["German", "Italian"]
    assert normalizer.extract_languages("[EN+DE]") == ["English", "German"]


def test_extract_languages_none_or_empty(normalizer: LanguageNormalizer):
    """Verify None and blank strings return empty list."""
    assert normalizer.extract_languages(None) == []
    assert normalizer.extract_languages("") == []
    assert normalizer.extract_languages("   ") == []


@pytest.mark.parametrize(
    "query,item_langs,expected",
    [
        ("ja", ["Japanese"], True),
        ("jpn", ["Japanese"], True),
        ("japanese", ["Japanese"], True),
        ("JAPANESE", ["Japanese"], True),
        ("fre", ["English", "French"], True),
        ("fra", ["French"], True),
        ("fr", ["French"], True),
        ("de", ["English", "Japanese"], False),
        ("spa", ["English"], False),
    ],
)
def test_language_matching(
    normalizer: LanguageNormalizer, query: str, item_langs: list[str], expected: bool
):
    """Verify bidirectional ISO code and name matching."""
    assert normalizer.matches(item_langs, query) is expected
```

---

### 10. `tests/test_parser.py` (test, transform)

**Analog:** `tests/test_config.py:32-38, 92-133`

**Test Pattern**:
```python
"""Unit tests for human size, age interval, and date cutoff parsing utilities."""

from datetime import datetime, timezone

import pytest

from arr_oldies.exceptions import ParseError
from arr_oldies.inventory.parser import parse_age_cutoff, parse_date_cutoff, parse_size


@pytest.mark.parametrize(
    "input_str,expected_bytes",
    [
        ("500B", 500),
        ("500MB", 500 * 1000 * 1000),
        ("500MiB", 500 * 1024 * 1024),
        ("2GB", 2 * 1000 * 1000 * 1000),
        ("2GiB", 2 * 1024 * 1024 * 1024),
        ("1.5GB", int(1.5 * 1000 * 1000 * 1000)),
        ("1TB", 1000**4),
        ("1TiB", 1024**4),
    ],
)
def test_parse_size_valid(input_str: str, expected_bytes: int):
    """Verify valid human size strings parse to exact byte integers."""
    assert parse_size(input_str) == expected_bytes


def test_parse_size_invalid():
    """Verify invalid size strings raise ParseError with helpful messages."""
    with pytest.raises(ParseError) as exc_info:
        parse_size("invalid_size")
    assert "Invalid size specification" in str(exc_info.value)

    with pytest.raises(ParseError) as exc_info:
        parse_size("500PB")  # Unsupported unit
    assert "Unknown size unit" in str(exc_info.value)


@pytest.mark.parametrize(
    "input_str,expected_days",
    [
        ("30", 30),
        ("30d", 30),
        ("2w", 14),
        ("6m", 180),
        ("1y", 365),
    ],
)
def test_parse_age_cutoff_valid(input_str: str, expected_days: int):
    """Verify valid age strings parse to integer days."""
    assert parse_age_cutoff(input_str) == expected_days


def test_parse_age_cutoff_invalid():
    """Verify invalid age strings raise ParseError."""
    with pytest.raises(ParseError) as exc_info:
        parse_age_cutoff("bad_age")
    assert "Invalid age specification" in str(exc_info.value)


def test_parse_date_cutoff_valid():
    """Verify ISO date strings parse to UTC timezone-aware datetimes."""
    dt = parse_date_cutoff("2024-01-15")
    assert dt == datetime(2024, 1, 15, 0, 0, 0, tzinfo=timezone.utc)

    dt_iso = parse_date_cutoff("2024-01-15T14:30:00Z")
    assert dt_iso == datetime(2024, 1, 15, 14, 30, 0, tzinfo=timezone.utc)
```

---

### 11. `tests/test_inventory_models.py` (test, transform)

**Analog:** `tests/test_api_models.py:56-101`

**Test Pattern**:
```python
"""Unit tests for MediaInventoryItem, InventoryFilter, and InventorySummary models."""

from datetime import datetime, timezone

from arr_oldies.inventory.models import (
    HistoryStatus,
    InventoryFilter,
    InventorySummary,
    MediaInventoryItem,
    MediaType,
    SortDirection,
    SortKey,
)
from arr_oldies.models import InstanceType


def test_media_inventory_item_instantiation():
    """Verify MediaInventoryItem creation, UTC normalization, and field defaults."""
    item = MediaInventoryItem(
        id="radarr:101",
        instance_name="radarr-main",
        instance_type=InstanceType.RADARR,
        media_type=MediaType.MOVIE,
        title="Interstellar",
        year=2014,
        file_path="/movies/Interstellar (2014)/Interstellar (2014).mkv",
        size_bytes=15000000000,
        audio_languages=["English"],
        import_date=datetime(2024, 1, 1, 12, 0, 0),  # Naive should become UTC
        age_days=100,
    )
    assert item.id == "radarr:101"
    assert item.instance_name == "radarr-main"
    assert item.import_date.tzinfo == timezone.utc
    assert item.has_history is True
    assert item.is_legacy is False
    assert item.history_status == HistoryStatus.IMPORTED
```

---

### 12. `tests/test_correlator_radarr.py` (test, batch / transform)

**Analog:** `tests/test_history_fetcher.py:50-104`

**Test Pattern**:
```python
"""Unit tests for HistoryCorrelator with Radarr movie files and history events."""

from datetime import datetime, timezone

from arr_oldies.api.fetcher import InstanceMediaData
from arr_oldies.api.models import (
    MediaInfo,
    RadarrHistoryRecord,
    RadarrMovie,
    RadarrMovieFile,
)
from arr_oldies.inventory.correlator import HistoryCorrelator
from arr_oldies.inventory.models import HistoryStatus, MediaType
from arr_oldies.models import InstanceType


def test_correlate_radarr_movie_exact_file_id_match():
    """Verify correlation matches downloadFolderImported event by fileId."""
    movie = RadarrMovie(id=1, title="Inception", year=2010, path="/movies/Inception")
    movie_file = RadarrMovieFile(
        id=101,
        movie_id=1,
        relative_path="Inception.mkv",
        path="/movies/Inception/Inception.mkv",
        size=10000000000,
        date_added=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        media_info=MediaInfo(audio_languages="eng/fre"),
    )
    history = [
        RadarrHistoryRecord(
            id=501,
            movie_id=1,
            source_title="Inception.2010.BluRay",
            event_type="downloadFolderImported",
            date=datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
            download_id="dl_123",
            data={"fileId": "101", "importedPath": "/movies/Inception/Inception.mkv"},
        ),
        RadarrHistoryRecord(
            id=500,
            movie_id=1,
            source_title="Inception.2010.BluRay",
            event_type="grabbed",
            date=datetime(2024, 1, 1, 8, 0, 0, tzinfo=timezone.utc),
            download_id="dl_123",
        ),
    ]
    data = InstanceMediaData(
        instance_name="radarr-main",
        instance_type=InstanceType.RADARR,
        movies=[movie],
        movie_files=[movie_file],
        history_records=history,
    )

    correlator = HistoryCorrelator()
    ref_time = datetime(2024, 1, 11, 10, 0, 0, tzinfo=timezone.utc)
    items = correlator.correlate_instance(data, reference_time=ref_time)

    assert len(items) == 1
    item = items[0]
    assert item.title == "Inception"
    assert item.media_type == MediaType.MOVIE
    assert item.import_date == datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
    assert item.grab_date == datetime(2024, 1, 1, 8, 0, 0, tzinfo=timezone.utc)
    assert item.age_days == 10
    assert item.audio_languages == ["English", "French"]
    assert item.history_status == HistoryStatus.GRABBED_AND_IMPORTED
    assert item.has_history is True
    assert item.is_legacy is False
```

---

### 13. `tests/test_correlator_sonarr.py` (test, batch / transform)

**Analog:** `tests/test_history_fetcher.py:106-162` and `tests/test_api_models.py:140-205`

**Test Pattern**:
```python
"""Unit tests for HistoryCorrelator with Sonarr TV series and multi-episode files."""

from datetime import datetime, timezone

from arr_oldies.api.fetcher import InstanceMediaData
from arr_oldies.api.models import (
    MediaInfo,
    SonarrEpisode,
    SonarrEpisodeFile,
    SonarrHistoryRecord,
    SonarrSeries,
)
from arr_oldies.inventory.correlator import HistoryCorrelator
from arr_oldies.inventory.models import MediaType
from arr_oldies.models import InstanceType


def test_correlate_sonarr_multi_episode_file():
    """Verify Sonarr multi-episode files format formatted_episode as 'S01E01-E02'."""
    series = SonarrSeries(id=10, title="Breaking Bad", year=2008, path="/tv/Breaking Bad")
    ep_file = SonarrEpisodeFile(
        id=201,
        series_id=10,
        season_number=1,
        relative_path="Breaking Bad - S01E01-E02.mkv",
        path="/tv/Breaking Bad/Breaking Bad - S01E01-E02.mkv",
        size=3000000000,
        date_added=datetime(2024, 2, 1, 0, 0, 0, tzinfo=timezone.utc),
        media_info=MediaInfo(audio_languages="eng"),
    )
    episodes = [
        SonarrEpisode(
            id=301,
            series_id=10,
            episode_file_id=201,
            season_number=1,
            episode_number=1,
            title="Pilot",
        ),
        SonarrEpisode(
            id=302,
            series_id=10,
            episode_file_id=201,
            season_number=1,
            episode_number=2,
            title="Cat's in the Bag",
        ),
    ]
    history = [
        SonarrHistoryRecord(
            id=9001,
            series_id=10,
            episode_id=301,
            source_title="Breaking.Bad.S01E01E02",
            event_type="downloadFolderImported",
            date=datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc),
            data={"fileId": "201"},
        )
    ]
    data = InstanceMediaData(
        instance_name="sonarr-tv",
        instance_type=InstanceType.SONARR,
        series=[series],
        episode_files=[ep_file],
        episodes=episodes,
        history_records=history,
    )

    correlator = HistoryCorrelator()
    items = correlator.correlate_instance(data)

    assert len(items) == 1
    item = items[0]
    assert item.media_type == MediaType.EPISODE
    assert item.title == "Breaking Bad"
    assert item.formatted_episode == "S01E01-E02"
    assert item.episode_numbers == [1, 2]
    assert item.episode_ids == [301, 302]
```

---

### 14. `tests/test_correlator_legacy.py` (test, batch / transform)

**Analog:** `tests/test_history_fetcher.py:164-208`

**Test Pattern**:
```python
"""Unit tests for legacy media items fallback when History API records are missing (INVT-06)."""

from datetime import datetime, timezone

from arr_oldies.api.fetcher import InstanceMediaData
from arr_oldies.api.models import RadarrMovie, RadarrMovieFile
from arr_oldies.inventory.correlator import HistoryCorrelator
from arr_oldies.inventory.models import HistoryStatus
from arr_oldies.models import InstanceType


def test_correlate_legacy_file_without_history():
    """Verify files with no history events fall back to date_added and are tagged as legacy."""
    movie = RadarrMovie(id=5, title="Classic Film", year=1980, path="/movies/Classic Film (1980)")
    movie_file = RadarrMovieFile(
        id=505,
        movie_id=5,
        relative_path="Classic Film (1980).mkv",
        path="/movies/Classic Film (1980)/Classic Film (1980).mkv",
        size=4000000000,
        date_added=datetime(2020, 5, 10, 15, 0, 0, tzinfo=timezone.utc),
    )
    data = InstanceMediaData(
        instance_name="radarr-main",
        instance_type=InstanceType.RADARR,
        movies=[movie],
        movie_files=[movie_file],
        history_records=[],  # Empty history
    )

    correlator = HistoryCorrelator()
    ref_time = datetime(2020, 5, 20, 15, 0, 0, tzinfo=timezone.utc)
    items = correlator.correlate_instance(data, reference_time=ref_time)

    assert len(items) == 1
    item = items[0]
    assert item.is_legacy is True
    assert item.has_history is False
    assert item.history_status == HistoryStatus.LEGACY
    assert item.import_date == datetime(2020, 5, 10, 15, 0, 0, tzinfo=timezone.utc)
    assert item.grab_date is None
    assert item.age_days == 10
```

---

### 15. `tests/test_inventory_engine.py` (test, batch / transform)

**Analog:** `tests/test_targeting.py:10-48` and `tests/test_history_fetcher.py:164-208`

**Test Pattern**:
```python
"""Unit tests for InventoryEngine filtering, sorting, and summary metrics."""

from datetime import datetime, timezone

import pytest

from arr_oldies.inventory.engine import InventoryEngine
from arr_oldies.inventory.models import (
    InventoryFilter,
    MediaInventoryItem,
    MediaType,
    SortDirection,
    SortKey,
)
from arr_oldies.models import InstanceType


@pytest.fixture
def sample_items() -> list[MediaInventoryItem]:
    return [
        MediaInventoryItem(
            id="radarr:1",
            instance_name="radarr-main",
            instance_type=InstanceType.RADARR,
            media_type=MediaType.MOVIE,
            title="Old Movie",
            size_bytes=1000000000,  # 1GB
            audio_languages=["Japanese"],
            import_date=datetime(2021, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            age_days=1000,
            has_history=True,
            is_legacy=False,
        ),
        MediaInventoryItem(
            id="sonarr:2",
            instance_name="sonarr-tv",
            instance_type=InstanceType.SONARR,
            media_type=MediaType.EPISODE,
            title="New Show",
            size_bytes=5000000000,  # 5GB
            audio_languages=["English", "French"],
            import_date=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            age_days=50,
            has_history=True,
            is_legacy=False,
        ),
        MediaInventoryItem(
            id="radarr:3",
            instance_name="radarr-4k",
            instance_type=InstanceType.RADARR,
            media_type=MediaType.MOVIE,
            title="Legacy Movie",
            size_bytes=20000000000,  # 20GB
            audio_languages=["English"],
            import_date=datetime(2020, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            age_days=1400,
            has_history=False,
            is_legacy=True,
        ),
    ]


def test_filter_by_audio_language(sample_items: list[MediaInventoryItem]):
    """Verify filtering by audio language matches canonical names and codes."""
    engine = InventoryEngine()
    filtered = engine.filter_inventory(sample_items, InventoryFilter(audio_langs=["ja"]))
    assert len(filtered) == 1
    assert filtered[0].title == "Old Movie"

    filtered_fr = engine.filter_inventory(sample_items, InventoryFilter(audio_langs=["fre"]))
    assert len(filtered_fr) == 1
    assert filtered_fr[0].title == "New Show"


def test_filter_by_min_size(sample_items: list[MediaInventoryItem]):
    """Verify filtering by minimum size in bytes."""
    engine = InventoryEngine()
    filtered = engine.filter_inventory(
        sample_items, InventoryFilter(min_size_bytes=2 * 1000 * 1000 * 1000)
    )
    assert len(filtered) == 2
    assert {i.title for i in filtered} == {"New Show", "Legacy Movie"}


def test_sort_inventory_oldest_first(sample_items: list[MediaInventoryItem]):
    """Verify sorting by oldest import date (default)."""
    engine = InventoryEngine()
    sorted_items = engine.sort_inventory(
        sample_items, sort_key=SortKey.IMPORT_DATE, direction=SortDirection.ASC
    )
    assert [i.title for i in sorted_items] == ["Legacy Movie", "Old Movie", "New Show"]


def test_generate_summary(sample_items: list[MediaInventoryItem]):
    """Verify summary metrics calculation across mixed items."""
    engine = InventoryEngine()
    summary = engine.generate_summary(sample_items)
    assert summary.total_items == 3
    assert summary.movie_count == 2
    assert summary.episode_count == 1
    assert summary.legacy_count == 1
    assert summary.total_size_bytes == 26000000000
    assert summary.instances_breakdown == {"radarr-main": 1, "sonarr-tv": 1, "radarr-4k": 1}
```

---

## Shared Patterns

### 1. Pydantic v2 Models & Schema Conventions
**Source:** `src/arr_oldies/api/models.py:9-13` and `src/arr_oldies/models.py:42-64`  
**Apply to:** `src/arr_oldies/inventory/models.py`
```python
from pydantic import BaseModel, ConfigDict, Field


class ApiBaseModel(BaseModel):
    """Base model configured to ignore extra fields for forward compatibility."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)
```

### 2. Timezone-Aware UTC Datetime Handling
**Source:** `src/arr_oldies/api/models.py:3-4` and `src/arr_oldies/targeting.py`  
**Apply to:** All inventory modules (`models.py`, `correlator.py`, `engine.py`, `parser.py`)
```python
from datetime import datetime, timezone

# Reference time instantiation
now_utc = datetime.now(timezone.utc)

# Validation / Normalization
if dt.tzinfo is None:
    dt = dt.replace(tzinfo=timezone.utc)
else:
    dt = dt.astimezone(timezone.utc)
```

### 3. Exception Hierarchy & Error Raising
**Source:** `src/arr_oldies/exceptions.py:1-40`  
**Apply to:** `src/arr_oldies/inventory/parser.py`, `correlator.py`, `engine.py`
```python
from arr_oldies.exceptions import ArrOldiesError


class InventoryError(ArrOldiesError):
    """Base exception for inventory correlation and processing errors."""


class ParseError(ArrOldiesError):
    """Raised when parsing human size, age, or date filter strings fails."""
```

### 4. Pytest Test File Organization & Assertion Patterns
**Source:** `tests/test_api_models.py:1-20`, `tests/test_targeting.py:1-40`, `tests/test_history_fetcher.py:1-25`  
**Apply to:** All new test files in `tests/test_*.py`
- Docstring explaining test suite focus
- Explicit fixtures generating typed domain models
- Parametrized tests via `@pytest.mark.parametrize`
- Targeted `with pytest.raises(...)` for error conditions
- Strict type hints and clean assertion diagnostics

---

## No Analog Found

*None.* Every file planned for Phase 3 has a direct or high-quality role-matched analog in the existing codebase.

---

## Metadata

**Analog search scope:** `src/arr_oldies/`, `tests/`  
**Files scanned:** 22 source and test files  
**Pattern extraction date:** 2026-08-23  
