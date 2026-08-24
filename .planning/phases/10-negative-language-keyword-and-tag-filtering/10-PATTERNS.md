# Phase 10: Negative Language, Title, and Tag Filtering — Pattern Map

**Mapped:** 2026-08-24  
**Files analyzed:** 20 (10 source/doc files, 10 test files)  
**Analogs found:** 20 / 20 (100% matched)  

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `src/arr_oldies/constants.py` | config / utility | request-response | `src/arr_oldies/constants.py:40-59` | exact |
| `src/arr_oldies/api/models.py` | model | transform | `src/arr_oldies/api/models.py:9-31, 50-63, 97-107` | exact |
| `src/arr_oldies/api/radarr.py` | service | request-response | `src/arr_oldies/api/radarr.py:26-36` | exact |
| `src/arr_oldies/api/sonarr.py` | service | request-response | `src/arr_oldies/api/sonarr.py:30-40` | exact |
| `src/arr_oldies/api/fetcher.py` | service | batch / transform | `src/arr_oldies/api/fetcher.py:26-120` | exact |
| `src/arr_oldies/inventory/models.py` | model | transform | `src/arr_oldies/inventory/models.py:44-110` | exact |
| `src/arr_oldies/inventory/correlator.py` | service | batch / transform | `src/arr_oldies/inventory/correlator.py:136-248, 250-423` | exact |
| `src/arr_oldies/inventory/engine.py` | service / controller | batch / transform | `src/arr_oldies/inventory/engine.py:23-101` | exact |
| `src/arr_oldies/cli.py` | controller | request-response | `src/arr_oldies/cli.py:210-377, 526-704` | exact |
| `README.md` | config / documentation | transform | `README.md:21-33, 57-85` | exact |
| `tests/test_api_models.py` | test | transform | `tests/test_api_models.py:50-80` | exact |
| `tests/test_radarr_client.py` | test | request-response | `tests/test_radarr_client.py:22-60` | exact |
| `tests/test_sonarr_client.py` | test | request-response | `tests/test_sonarr_client.py:22-60` | exact |
| `tests/test_history_fetcher.py` | test | batch / transform | `tests/test_history_fetcher.py:45-120` | exact |
| `tests/test_correlator_radarr.py` | test | batch / transform | `tests/test_correlator_radarr.py:19-65` | exact |
| `tests/test_correlator_sonarr.py` | test | batch / transform | `tests/test_correlator_sonarr.py:18-65` | exact |
| `tests/test_inventory_models.py` | test | transform | `tests/test_inventory_models.py:23-80` | exact |
| `tests/test_inventory_engine.py` | test | batch / transform | `tests/test_inventory_engine.py:19-150` | exact |
| `tests/test_cli_scan.py` | test | request-response | `tests/test_cli_scan.py:14-80` | exact |
| `tests/test_cli_clean.py` | test | request-response | `tests/test_cli_clean.py:15-80` | exact |

---

## Source Pattern Assignments

### 1. `src/arr_oldies/constants.py` (config / utility, request-response)

**Analog:** `src/arr_oldies/constants.py:40-59`

**Constants Extension Pattern** (derived from existing Radarr and Sonarr endpoint declarations):
```python
# *arr API endpoints (per D-05, API-01, API-02)
API_STATUS_ENDPOINT: str = "/api/v3/system/status"

# Radarr endpoints (API-01, INVT-09)
RADARR_MOVIE_ENDPOINT: str = "/api/v3/movie"
RADARR_MOVIEFILE_ENDPOINT: str = "/api/v3/moviefile"
RADARR_HISTORY_ENDPOINT: str = "/api/v3/history"
RADARR_HISTORY_MOVIE_ENDPOINT: str = "/api/v3/history/movie"
RADARR_TAG_ENDPOINT: str = "/api/v3/tag"

# Sonarr endpoints (API-02, INVT-09)
SONARR_SERIES_ENDPOINT: str = "/api/v3/series"
SONARR_EPISODEFILE_ENDPOINT: str = "/api/v3/episodefile"
SONARR_EPISODE_ENDPOINT: str = "/api/v3/episode"
SONARR_HISTORY_ENDPOINT: str = "/api/v3/history"
SONARR_HISTORY_SERIES_ENDPOINT: str = "/api/v3/history/series"
SONARR_TAG_ENDPOINT: str = "/api/v3/tag"
```

---

### 2. `src/arr_oldies/api/models.py` (model, transform)

**Analog:** `src/arr_oldies/api/models.py:9-31, 50-63, 97-107`

**Tag Model and Schema Extension Pattern**:
```python
"""Pydantic v2 schemas for Radarr and Sonarr REST API responses."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ApiBaseModel(BaseModel):
    """Base model configured to ignore extra fields for API forward compatibility."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)


class Tag(ApiBaseModel):
    """Tag definition in Radarr or Sonarr (INVT-09)."""

    id: int
    label: str


class RadarrMovie(ApiBaseModel):
    """Radarr movie library entry."""

    id: int
    title: str
    year: int = Field(default=0)
    path: str = Field(default="")
    monitored: bool = Field(default=True)
    has_file: bool = Field(default=False, alias="hasFile")
    movie_file_id: int | None = Field(default=None, alias="movieFileId")
    movie_file: RadarrMovieFile | None = Field(default=None, alias="movieFile")
    size_on_disk: int | None = Field(default=None, alias="sizeOnDisk")
    genres: list[str] = Field(default_factory=list)
    tags: list[int] = Field(default_factory=list)


class SonarrSeries(ApiBaseModel):
    """Sonarr series library entry."""

    id: int
    title: str
    year: int = Field(default=0)
    path: str = Field(default="")
    monitored: bool = Field(default=True)
    seasons: list[SonarrSeason] = Field(default_factory=list)
    statistics: dict[str, Any] | None = Field(default=None)
    tags: list[int] = Field(default_factory=list)
```

---

### 3. `src/arr_oldies/api/radarr.py` (service, request-response)

**Analog:** `src/arr_oldies/api/radarr.py:23-36`

**Async API Method Pattern**:
```python
from arr_oldies.api.models import (
    RadarrHistoryPage,
    RadarrHistoryRecord,
    RadarrMovie,
    RadarrMovieFile,
    Tag,
)
from arr_oldies.constants import (
    DEFAULT_HISTORY_PAGE_SIZE,
    RADARR_HISTORY_ENDPOINT,
    RADARR_HISTORY_MOVIE_ENDPOINT,
    RADARR_MOVIE_ENDPOINT,
    RADARR_MOVIEFILE_ENDPOINT,
    RADARR_TAG_ENDPOINT,
)


class RadarrClient(BaseArrClient):
    """Async API client for Radarr v3/v4 instances."""

    async def get_tags(self) -> list[Tag]:
        """Retrieve all tag definitions in the Radarr instance (INVT-09)."""
        response = await self.get(RADARR_TAG_ENDPOINT)
        data = response.json()
        return [Tag.model_validate(item) for item in data]
```

---

### 4. `src/arr_oldies/api/sonarr.py` (service, request-response)

**Analog:** `src/arr_oldies/api/sonarr.py:27-40`

**Async API Method Pattern**:
```python
from arr_oldies.api.models import (
    SonarrEpisode,
    SonarrEpisodeFile,
    SonarrHistoryPage,
    SonarrHistoryRecord,
    SonarrSeries,
    Tag,
)
from arr_oldies.constants import (
    DEFAULT_HISTORY_PAGE_SIZE,
    DEFAULT_SERIES_CONCURRENCY,
    SONARR_EPISODE_ENDPOINT,
    SONARR_EPISODEFILE_ENDPOINT,
    SONARR_HISTORY_ENDPOINT,
    SONARR_HISTORY_SERIES_ENDPOINT,
    SONARR_SERIES_ENDPOINT,
    SONARR_TAG_ENDPOINT,
)


class SonarrClient(BaseArrClient):
    """Async API client for Sonarr v3/v4 instances."""

    async def get_tags(self) -> list[Tag]:
        """Retrieve all tag definitions in the Sonarr instance (INVT-09)."""
        response = await self.get(SONARR_TAG_ENDPOINT)
        data = response.json()
        return [Tag.model_validate(item) for item in data]
```

---

### 5. `src/arr_oldies/api/fetcher.py` (service, batch / transform)

**Analog:** `src/arr_oldies/api/fetcher.py:26-120`

**Multi-Instance Resilient Fetcher Pattern with Tag Resolution**:
```python
from arr_oldies.api.models import (
    RadarrHistoryRecord,
    RadarrMovie,
    RadarrMovieFile,
    SonarrEpisode,
    SonarrEpisodeFile,
    SonarrHistoryRecord,
    SonarrSeries,
    Tag,
)


class InstanceMediaData(BaseModel):
    """Aggregated media and history data retrieved from a single *arr instance."""

    instance_name: str
    instance_type: InstanceType
    movies: list[RadarrMovie] = Field(default_factory=list)
    movie_files: list[RadarrMovieFile] = Field(default_factory=list)
    series: list[SonarrSeries] = Field(default_factory=list)
    episode_files: list[SonarrEpisodeFile] = Field(default_factory=list)
    episodes: list[SonarrEpisode] = Field(default_factory=list)
    tags: list[Tag] = Field(default_factory=list)
    history_records: list[RadarrHistoryRecord] | list[SonarrHistoryRecord] = Field(
        default_factory=list
    )


class MultiInstanceFetcher:
    """Orchestrates resilient, concurrent scans across multiple Radarr/Sonarr instances."""

    async def fetch_instance_data(
        self,
        instance: InstanceConfig,
        history_page_size: int = DEFAULT_HISTORY_PAGE_SIZE,
        progress_callback: Callable[[str, int, int, int, int], None] | None = None,
    ) -> InstanceFetchResult:
        """Fetch media library, tags, and history records for a single instance with error isolation."""
        start_time = time.perf_counter()

        def _history_progress(
            page: int, total_pages: int, total_records: int, fetched: int
        ) -> None:
            if progress_callback is not None:
                progress_callback(instance.name, page, total_pages, total_records, fetched)

        try:
            client = create_client(instance)
            async with client:
                if isinstance(client, RadarrClient):
                    movies = await client.get_movies()
                    movie_files = [m.movie_file for m in movies if m.movie_file is not None]
                    if not movie_files:
                        try:
                            movie_files = await client.get_movie_files()
                        except Exception:  # noqa: BLE001
                            movie_files = []

                    # Resilient tag retrieval with empty list fallback
                    try:
                        tags = await client.get_tags()
                    except Exception:  # noqa: BLE001
                        tags = []

                    radarr_history = await client.fetch_all_history(
                        page_size=history_page_size,
                        progress_callback=_history_progress,
                    )

                    data = InstanceMediaData(
                        instance_name=instance.name,
                        instance_type=instance.type,
                        movies=movies,
                        movie_files=movie_files,
                        tags=tags,
                        history_records=radarr_history,
                    )
                    item_count = len(movie_files) or len(movies)

                elif isinstance(client, SonarrClient):
                    series = await client.get_series()
                    series_ids = [s.id for s in series]

                    async def _safe_get_tags() -> list[Tag]:
                        try:
                            return await client.get_tags()
                        except Exception:  # noqa: BLE001
                            return []

                    episode_files, episodes, sonarr_history, tags = await asyncio.gather(
                        client.get_all_episode_files(series_ids=series_ids),
                        client.get_all_episodes(series_ids=series_ids),
                        client.fetch_all_history(
                            page_size=history_page_size,
                            progress_callback=_history_progress,
                        ),
                        _safe_get_tags(),
                    )
                    data = InstanceMediaData(
                        instance_name=instance.name,
                        instance_type=instance.type,
                        series=series,
                        episodes=episodes,
                        episode_files=episode_files,
                        tags=tags,
                        history_records=sonarr_history,
                    )
                    item_count = len(episode_files) or len(series)
                else:
                    raise TypeError(f"Unknown instance type '{instance.type}'")

            latency_ms = (time.perf_counter() - start_time) * 1000.0
            return InstanceFetchResult(
                instance_name=instance.name,
                instance_type=instance.type,
                url=instance.url,
                success=True,
                data=data,
                item_count=item_count,
                latency_ms=round(latency_ms, 2),
            )
```

---

### 6. `src/arr_oldies/inventory/models.py` (model, transform)

**Analog:** `src/arr_oldies/inventory/models.py:44-110`

**Inventory Models Extension Pattern**:
```python
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
    tags: list[str] = Field(
        default_factory=list,
        description="Resolved tag labels assigned to media item (INVT-09)",
    )
    import_date: datetime
    grab_date: datetime | None = None
    age_days: int = 0
    monitored: bool = True
    has_history: bool = True
    is_legacy: bool = False
    history_status: HistoryStatus = HistoryStatus.IMPORTED
    source_title: str | None = None
    download_id: str | None = None


class InventoryFilter(BaseModel):
    """Filter criteria applied to in-memory media inventory."""

    model_config = ConfigDict(extra="ignore")

    media_types: list[MediaType] | None = None
    instance_names: list[str] | None = None
    audio_langs: list[str] | None = None
    not_audio_langs: list[str] | None = None
    titles: list[str] | None = None
    tags: list[str] | None = None
    not_tags: list[str] | None = None
    min_size_bytes: int | None = None
    max_size_bytes: int | None = None
    min_age_days: int | None = None
    max_age_days: int | None = None
    before_date: datetime | None = None
    after_date: datetime | None = None
    legacy_only: bool = False
    history_only: bool = False
    monitored_only: bool = False
    unmonitored_only: bool = False
```

---

### 7. `src/arr_oldies/inventory/correlator.py` (service, batch / transform)

**Analog:** `src/arr_oldies/inventory/correlator.py:136-248, 250-423`

**Dynamic Tag Label Resolution Pattern**:
```python
class HistoryCorrelator:
    """Correlates media files with History API events and standardizes inventory items."""

    def _correlate_radarr(
        self,
        instance_data: InstanceMediaData,
        now_utc: datetime,
    ) -> list[MediaInventoryItem]:
        """Correlate Radarr movie files with history events and resolve tag labels."""
        movies_by_id: dict[int, RadarrMovie] = {m.id: m for m in instance_data.movies}
        tags_by_id: dict[int, str] = {t.id: t.label for t in instance_data.tags}
        index = RadarrHistoryIndex(instance_data.history_records)
        items: list[MediaInventoryItem] = []

        for movie_file in instance_data.movie_files:
            movie = movies_by_id.get(movie_file.movie_id)
            title = (
                movie.title
                if movie
                else (movie_file.relative_path or f"Movie {movie_file.movie_id}")
            )
            year = movie.year if movie else None
            monitored = movie.monitored if movie is not None else True
            movie_tags = (
                [tags_by_id[tid] for tid in movie.tags if tid in tags_by_id]
                if movie and movie.tags
                else []
            )

            # Audio languages extraction
            raw_audio = movie_file.media_info.audio_languages if movie_file.media_info else None
            audio_languages = (
                self.normalizer.extract_languages(raw_audio) if movie_file.media_info else []
            )
            video_codec = movie_file.media_info.video_codec if movie_file.media_info else None
            resolution = movie_file.media_info.resolution if movie_file.media_info else None

            # Match import event
            candidate_imports: list[RadarrHistoryRecord] = []
            if movie_file.id in index.imports_by_file_id:
                candidate_imports = index.imports_by_file_id[movie_file.id]
            elif movie_file.path and movie_file.path.strip().lower() in index.imports_by_path:
                candidate_imports = index.imports_by_path[movie_file.path.strip().lower()]
            elif movie_file.movie_id in index.imports_by_movie_id:
                candidate_imports = index.imports_by_movie_id[movie_file.movie_id]

            if candidate_imports:
                import_event = max(candidate_imports, key=lambda r: r.date)
                import_date = import_event.date
                download_id = import_event.download_id
                source_title = import_event.source_title
                has_history = True
                is_legacy = False

                grab_event: RadarrHistoryRecord | None = None
                if download_id and download_id in index.grabs_by_download_id:
                    grab_event = index.grabs_by_download_id[download_id]
                else:
                    movie_grabs = [
                        r
                        for r in index.grabs_by_movie_id.get(movie_file.movie_id, [])
                        if r.date <= import_date
                    ]
                    if movie_grabs:
                        grab_event = max(movie_grabs, key=lambda r: r.date)

                if grab_event:
                    grab_date = grab_event.date
                    history_status = HistoryStatus.GRABBED_AND_IMPORTED
                    if not source_title and grab_event.source_title:
                        source_title = grab_event.source_title
                else:
                    grab_date = None
                    history_status = HistoryStatus.IMPORTED
            else:
                import_date = movie_file.date_added
                grab_date = None
                has_history = False
                is_legacy = True
                history_status = HistoryStatus.LEGACY
                download_id = None
                source_title = None

            if import_date.tzinfo is None:
                import_date_utc = import_date.replace(tzinfo=UTC)
            else:
                import_date_utc = import_date.astimezone(UTC)
            age_days = max(0, (now_utc - import_date_utc).days)

            item = MediaInventoryItem(
                id=f"{instance_data.instance_name}:{movie_file.id}",
                instance_name=instance_data.instance_name,
                instance_type=instance_data.instance_type,
                media_type=MediaType.MOVIE,
                title=title,
                year=year,
                movie_id=movie_file.movie_id,
                movie_file_id=movie_file.id,
                file_path=movie_file.path,
                relative_path=movie_file.relative_path,
                size_bytes=movie_file.size,
                audio_languages=audio_languages,
                raw_audio_languages=raw_audio,
                video_codec=video_codec,
                resolution=resolution,
                tags=movie_tags,
                import_date=import_date,
                grab_date=grab_date,
                age_days=age_days,
                monitored=monitored,
                has_history=has_history,
                is_legacy=is_legacy,
                history_status=history_status,
                source_title=source_title,
                download_id=download_id,
            )
            items.append(item)

        return items

    def _correlate_sonarr(
        self,
        instance_data: InstanceMediaData,
        now_utc: datetime,
    ) -> list[MediaInventoryItem]:
        """Correlate Sonarr episode files with history events and resolve series tag labels."""
        series_by_id: dict[int, SonarrSeries] = {s.id: s for s in instance_data.series}
        tags_by_id: dict[int, str] = {t.id: t.label for t in instance_data.tags}
        episodes_by_file_id: dict[int, list[SonarrEpisode]] = defaultdict(list)
        for ep in instance_data.episodes:
            if ep.episode_file_id is not None:
                episodes_by_file_id[ep.episode_file_id].append(ep)

        index = SonarrHistoryIndex(instance_data.history_records)
        items: list[MediaInventoryItem] = []

        for ep_file in instance_data.episode_files:
            series = series_by_id.get(ep_file.series_id)
            title = (
                series.title if series else (ep_file.relative_path or f"Series {ep_file.series_id}")
            )
            year = series.year if series else None
            series_tags = (
                [tags_by_id[tid] for tid in series.tags if tid in tags_by_id]
                if series and series.tags
                else []
            )

            episodes = episodes_by_file_id.get(ep_file.id, [])
            ep_numbers = sorted(e.episode_number for e in episodes)
            ep_ids = [e.id for e in episodes]
            monitored = (
                any(ep.monitored for ep in episodes)
                if episodes
                else (series.monitored if series is not None else True)
            )

            if len(ep_numbers) > 1:
                formatted_episode = (
                    f"S{ep_file.season_number:02d}E{ep_numbers[0]:02d}-E{ep_numbers[-1]:02d}"
                )
            elif ep_numbers:
                formatted_episode = f"S{ep_file.season_number:02d}E{ep_numbers[0]:02d}"
            else:
                path_to_check = ep_file.relative_path or ep_file.path or ""
                match = re.search(
                    r"[Ss](\d+)[Ee](\d+)(?:[ -]*[Ee](\d+))?",
                    path_to_check,
                )
                if match:
                    s_num = int(match.group(1))
                    e_start = int(match.group(2))
                    e_end = int(match.group(3)) if match.group(3) else None
                    if e_end:
                        formatted_episode = f"S{s_num:02d}E{e_start:02d}-E{e_end:02d}"
                    else:
                        formatted_episode = f"S{s_num:02d}E{e_start:02d}"
                else:
                    formatted_episode = f"S{ep_file.season_number:02d}"

            episode_title = (
                episodes[0].title if (len(episodes) == 1 and episodes[0].title) else None
            )

            raw_audio = ep_file.media_info.audio_languages if ep_file.media_info else None
            audio_languages = (
                self.normalizer.extract_languages(raw_audio) if ep_file.media_info else []
            )
            video_codec = ep_file.media_info.video_codec if ep_file.media_info else None
            resolution = ep_file.media_info.resolution if ep_file.media_info else None

            candidate_imports: list[SonarrHistoryRecord] = []
            if ep_file.id in index.imports_by_file_id:
                candidate_imports = index.imports_by_file_id[ep_file.id]
            elif ep_file.path and ep_file.path.strip().lower() in index.imports_by_path:
                candidate_imports = index.imports_by_path[ep_file.path.strip().lower()]
            elif ep_ids:
                for eid in ep_ids:
                    candidate_imports.extend(index.imports_by_episode_id.get(eid, []))

            if candidate_imports:
                import_event = max(candidate_imports, key=lambda r: r.date)
                import_date = import_event.date
                download_id = import_event.download_id
                source_title = import_event.source_title
                has_history = True
                is_legacy = False
                if not ep_ids and import_event.episode_id:
                    ep_ids = [import_event.episode_id]

                grab_event: SonarrHistoryRecord | None = None
                if download_id and download_id in index.grabs_by_download_id:
                    grab_event = index.grabs_by_download_id[download_id]
                elif ep_ids:
                    candidate_grabs: list[SonarrHistoryRecord] = []
                    for eid in ep_ids:
                        candidate_grabs.extend(index.grabs_by_episode_id.get(eid, []))
                    valid_grabs = [r for r in candidate_grabs if r.date <= import_date]
                    if valid_grabs:
                        grab_event = max(valid_grabs, key=lambda r: r.date)
                    else:
                        series_grabs = [
                            r
                            for r in index.grabs_by_series_id.get(ep_file.series_id, [])
                            if r.date <= import_date
                        ]
                        if series_grabs:
                            grab_event = max(series_grabs, key=lambda r: r.date)
                else:
                    series_grabs = [
                        r
                        for r in index.grabs_by_series_id.get(ep_file.series_id, [])
                        if r.date <= import_date
                    ]
                    if series_grabs:
                        grab_event = max(series_grabs, key=lambda r: r.date)

                if grab_event:
                    grab_date = grab_event.date
                    history_status = HistoryStatus.GRABBED_AND_IMPORTED
                    if not source_title and grab_event.source_title:
                        source_title = grab_event.source_title
                else:
                    grab_date = None
                    history_status = HistoryStatus.IMPORTED
            else:
                import_date = ep_file.date_added
                grab_date = None
                has_history = False
                is_legacy = True
                history_status = HistoryStatus.LEGACY
                download_id = None
                source_title = None

            if import_date.tzinfo is None:
                import_date_utc = import_date.replace(tzinfo=UTC)
            else:
                import_date_utc = import_date.astimezone(UTC)
            age_days = max(0, (now_utc - import_date_utc).days)

            item = MediaInventoryItem(
                id=f"{instance_data.instance_name}:{ep_file.id}",
                instance_name=instance_data.instance_name,
                instance_type=instance_data.instance_type,
                media_type=MediaType.EPISODE,
                title=title,
                year=year,
                season_number=ep_file.season_number,
                episode_numbers=ep_numbers,
                formatted_episode=formatted_episode,
                episode_title=episode_title,
                series_id=ep_file.series_id,
                episode_file_id=ep_file.id,
                episode_ids=ep_ids,
                file_path=ep_file.path,
                relative_path=ep_file.relative_path,
                size_bytes=ep_file.size,
                audio_languages=audio_languages,
                raw_audio_languages=raw_audio,
                video_codec=video_codec,
                resolution=resolution,
                tags=series_tags,
                import_date=import_date,
                grab_date=grab_date,
                age_days=age_days,
                monitored=monitored,
                has_history=has_history,
                is_legacy=is_legacy,
                history_status=history_status,
                source_title=source_title,
                download_id=download_id,
            )
            items.append(item)

        return items
```

---

### 8. `src/arr_oldies/inventory/engine.py` (service / controller, batch / transform)

**Analog:** `src/arr_oldies/inventory/engine.py:23-101`

**Composable Multi-Filter Pattern**:
```python
class InventoryEngine:
    """Orchestrates inventory filtering, sorting, and aggregate summary generation."""

    def filter_inventory(
        self,
        items: list[MediaInventoryItem],
        criteria: InventoryFilter,
    ) -> list[MediaInventoryItem]:
        """Filter media inventory items matching all specified criteria in a single pass."""
        filtered: list[MediaInventoryItem] = []

        norm_instances: set[str] | None = None
        if criteria.instance_names:
            norm_instances = {n.strip().lower() for n in criteria.instance_names}

        before_date = criteria.before_date
        if before_date is not None:
            before_date = before_date.replace(tzinfo=UTC) if before_date.tzinfo is None else before_date.astimezone(UTC)

        after_date = criteria.after_date
        if after_date is not None:
            after_date = after_date.replace(tzinfo=UTC) if after_date.tzinfo is None else after_date.astimezone(UTC)

        for item in items:
            # 1. Media Type Filter
            if criteria.media_types and item.media_type not in criteria.media_types:
                continue

            # 2. Instance Filter
            if norm_instances is not None and item.instance_name.strip().lower() not in norm_instances:
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
            if before_date is not None and item.import_date >= before_date:
                continue
            if after_date is not None and item.import_date <= after_date:
                continue

            # 6. Legacy / History Filter
            if criteria.legacy_only and item.has_history:
                continue
            if criteria.history_only and not item.has_history:
                continue

            # 7. Monitored / Unmonitored Filter
            if criteria.monitored_only and not item.monitored:
                continue
            if criteria.unmonitored_only and item.monitored:
                continue

            # 8. Audio Language Positive Filter
            if criteria.audio_langs and not any(
                self.normalizer.matches(item.audio_languages, q) for q in criteria.audio_langs
            ):
                continue

            # 9. Audio Language Negative Filter (INVT-07)
            if criteria.not_audio_langs and any(
                self.normalizer.matches(item.audio_languages, q) for q in criteria.not_audio_langs
            ):
                continue

            # 10. Title Substring Filter (INVT-08)
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

            # 11. Tag Inclusion Filter (INVT-09)
            if criteria.tags:
                item_tags = {t.strip().lower() for t in item.tags}
                if not any(q.strip().lower() in item_tags for q in criteria.tags if q.strip()):
                    continue

            # 12. Tag Exclusion Filter (INVT-09)
            if criteria.not_tags:
                item_tags = {t.strip().lower() for t in item.tags}
                if any(q.strip().lower() in item_tags for q in criteria.not_tags if q.strip()):
                    continue

            filtered.append(item)

        return filtered
```

---

### 9. `src/arr_oldies/cli.py` (controller, request-response)

**Analog:** `src/arr_oldies/cli.py:210-377, 526-704`

**CLI Filter Parameter and Alias Mapping Pattern**:
```python
# Shared Typer options added to scan_command and clean_command:
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

# Bound to InventoryFilter in both commands:
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

---

### 10. `README.md` (config / documentation, transform)

**Analog:** `README.md:21-33, 57-85`

**Documentation Pattern for Advanced Filtering**:
```markdown
- **Audio Language Filtering & Exclusion**: Filter media by audio track language supporting ISO 639-1, ISO 639-2, standard language names, and common aliases (e.g. `-l ja`, `-l japanese`). Exclude media items with specific audio tracks using `--!l pt-br` or `--not-audio-lang por`.
- **Title Substring Matching**: Filter items case-insensitively by title substring (`--title "matrix"` or `--title "breaking"`) across movie, TV series, and episode titles.
- **Dynamic Tag Label Resolution**: Filter by instance tag labels for inclusion (`--tag 4k`) or exclusion (`--!tag archive`), automatically mapping friendly tag strings to internal instance tag IDs.
```

---

## Test Pattern Assignments

### 11. `tests/test_api_models.py` (test, transform)

**Analog:** `tests/test_api_models.py:50-80`

**Tag Model Validation Test Pattern**:
```python
from arr_oldies.api.models import RadarrMovie, SonarrSeries, Tag


def test_tag_model_parsing():
    """Verify Tag model parsing with integer id and string label."""
    data = {"id": 1, "label": "4k"}
    tag = Tag.model_validate(data)
    assert tag.id == 1
    assert tag.label == "4k"


def test_radarr_movie_and_sonarr_series_tags_parsing():
    """Verify RadarrMovie and SonarrSeries parse tags lists."""
    movie_data = {
        "id": 1,
        "title": "The Matrix",
        "tags": [1, 5],
    }
    movie = RadarrMovie.model_validate(movie_data)
    assert movie.tags == [1, 5]

    series_data = {
        "id": 2,
        "title": "Breaking Bad",
        "tags": [3],
    }
    series = SonarrSeries.model_validate(series_data)
    assert series.tags == [3]
```

---

### 12. `tests/test_radarr_client.py` (test, request-response)

**Analog:** `tests/test_radarr_client.py:22-60`

**Radarr Tag Endpoint Test Pattern**:
```python
@pytest.mark.asyncio
@respx.mock
async def test_radarr_get_tags(radarr_instance: InstanceConfig):
    """Verify get_tags fetches and deserializes Radarr tag definitions."""
    respx.get("http://radarr.local:7878/api/v3/tag").respond(
        json=[
            {"id": 1, "label": "4k"},
            {"id": 2, "label": "archive"},
        ]
    )

    async with RadarrClient(radarr_instance) as client:
        tags = await client.get_tags()
        assert len(tags) == 2
        assert tags[0].id == 1
        assert tags[0].label == "4k"
        assert tags[1].id == 2
        assert tags[1].label == "archive"
```

---

### 13. `tests/test_sonarr_client.py` (test, request-response)

**Analog:** `tests/test_sonarr_client.py:22-60`

**Sonarr Tag Endpoint Test Pattern**:
```python
@pytest.mark.asyncio
@respx.mock
async def test_sonarr_get_tags(sonarr_instance: InstanceConfig):
    """Verify get_tags fetches and deserializes Sonarr tag definitions."""
    respx.get("http://sonarr.local:8989/api/v3/tag").respond(
        json=[
            {"id": 10, "label": "anime"},
            {"id": 20, "label": "favorite"},
        ]
    )

    async with SonarrClient(sonarr_instance) as client:
        tags = await client.get_tags()
        assert len(tags) == 2
        assert tags[0].id == 10
        assert tags[0].label == "anime"
        assert tags[1].id == 20
        assert tags[1].label == "favorite"
```

---

### 14. `tests/test_history_fetcher.py` (test, batch / transform)

**Analog:** `tests/test_history_fetcher.py:45-120`

**Resilient Tag Acquisition Test Pattern**:
```python
@pytest.mark.asyncio
@respx.mock
async def test_fetch_instance_data_with_tags_and_fallback(radarr_inst: InstanceConfig):
    """Verify MultiInstanceFetcher acquires tags or falls back gracefully on tag API error."""
    respx.get("http://radarr-hd.local:7878/api/v3/movie").respond(
        json=[{"id": 1, "title": "Movie 1", "tags": [1]}]
    )
    respx.get("http://radarr-hd.local:7878/api/v3/moviefile").respond(json=[])
    respx.get("http://radarr-hd.local:7878/api/v3/history").respond(
        json={"page": 1, "pageSize": 1000, "totalRecords": 0, "records": []}
    )
    respx.get("http://radarr-hd.local:7878/api/v3/tag").respond(
        status_code=500  # Simulate tag API failure
    )

    fetcher = MultiInstanceFetcher()
    result = await fetcher.fetch_instance_data(radarr_inst)
    assert result.success is True
    assert result.data is not None
    assert result.data.tags == []
```

---

### 15. `tests/test_correlator_radarr.py` (test, batch / transform)

**Analog:** `tests/test_correlator_radarr.py:19-65`

**Radarr Tag Resolution Test Pattern**:
```python
def test_correlate_radarr_movie_tag_label_mapping():
    """Verify movie numeric tag IDs are mapped to string labels on MediaInventoryItem."""
    movie = RadarrMovie(
        id=1,
        title="Inception",
        year=2010,
        path="/movies/Inception (2010)",
        tags=[1, 2],
    )
    movie_file = RadarrMovieFile(
        id=101,
        movie_id=1,
        date_added=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
    )
    tags = [
        Tag(id=1, label="4k"),
        Tag(id=2, label="favorite"),
    ]
    data = InstanceMediaData(
        instance_name="radarr-main",
        instance_type=InstanceType.RADARR,
        movies=[movie],
        movie_files=[movie_file],
        tags=tags,
        history_records=[],
    )

    correlator = HistoryCorrelator()
    items = correlator.correlate_instance(data)
    assert len(items) == 1
    assert items[0].tags == ["4k", "favorite"]
```

---

### 16. `tests/test_correlator_sonarr.py` (test, batch / transform)

**Analog:** `tests/test_correlator_sonarr.py:18-65`

**Sonarr Series Tag Resolution Test Pattern**:
```python
def test_correlate_sonarr_series_tag_label_mapping():
    """Verify series numeric tag IDs propagate to episode MediaInventoryItem records."""
    series = SonarrSeries(
        id=10,
        title="Breaking Bad",
        year=2008,
        path="/tv/Breaking Bad",
        tags=[5],
    )
    ep_file = SonarrEpisodeFile(
        id=201,
        series_id=10,
        season_number=1,
        date_added=datetime(2024, 2, 1, 0, 0, 0, tzinfo=UTC),
    )
    episodes = [
        SonarrEpisode(id=301, series_id=10, episode_file_id=201, season_number=1, episode_number=1, title="Pilot"),
    ]
    tags = [Tag(id=5, label="drama")]
    data = InstanceMediaData(
        instance_name="sonarr-tv",
        instance_type=InstanceType.SONARR,
        series=[series],
        episode_files=[ep_file],
        episodes=episodes,
        tags=tags,
        history_records=[],
    )

    correlator = HistoryCorrelator()
    items = correlator.correlate_instance(data)
    assert len(items) == 1
    assert items[0].tags == ["drama"]
```

---

### 17. `tests/test_inventory_models.py` (test, transform)

**Analog:** `tests/test_inventory_models.py:23-80`

**Item and Filter Schema Test Pattern**:
```python
def test_inventory_item_and_filter_new_fields():
    """Verify MediaInventoryItem tags and InventoryFilter new filtering fields."""
    item = MediaInventoryItem(
        id="radarr:101",
        instance_name="radarr-main",
        instance_type=InstanceType.RADARR,
        media_type=MediaType.MOVIE,
        title="Interstellar",
        file_path="/movies/Interstellar/Interstellar.mkv",
        import_date=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
        tags=["4k", "sci-fi"],
    )
    assert item.tags == ["4k", "sci-fi"]

    crit = InventoryFilter(
        not_audio_langs=["pt-br"],
        titles=["matrix"],
        tags=["4k"],
        not_tags=["archive"],
    )
    assert crit.not_audio_langs == ["pt-br"]
    assert crit.titles == ["matrix"]
    assert crit.tags == ["4k"]
    assert crit.not_tags == ["archive"]
```

---

### 18. `tests/test_inventory_engine.py` (test, batch / transform)

**Analog:** `tests/test_inventory_engine.py:19-150`

**Negative Language, Title Substring, and Tag Filter Test Pattern**:
```python
def test_filter_negative_audio_language(sample_items: list[MediaInventoryItem]):
    """Verify items containing specified negative audio languages are excluded."""
    engine = InventoryEngine()

    # Exclude Japanese
    filtered = engine.filter_inventory(
        sample_items, InventoryFilter(not_audio_langs=["ja"])
    )
    assert not any("Japanese" in item.audio_languages for item in filtered)


def test_filter_title_substring_matching(sample_items: list[MediaInventoryItem]):
    """Verify case-insensitive substring title matching across title and episode_title."""
    engine = InventoryEngine()

    filtered = engine.filter_inventory(
        sample_items, InventoryFilter(titles=["anime"])
    )
    assert len(filtered) == 1
    assert "Anime" in filtered[0].title


def test_filter_tag_inclusion_and_exclusion():
    """Verify tag inclusion and exclusion filters."""
    engine = InventoryEngine()
    items = [
        MediaInventoryItem(
            id="1",
            instance_name="radarr",
            instance_type=InstanceType.RADARR,
            media_type=MediaType.MOVIE,
            title="Movie 1",
            file_path="/m1.mkv",
            import_date=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
            tags=["4K", "Remux"],
        ),
        MediaInventoryItem(
            id="2",
            instance_name="radarr",
            instance_type=InstanceType.RADARR,
            media_type=MediaType.MOVIE,
            title="Movie 2",
            file_path="/m2.mkv",
            import_date=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
            tags=["1080p", "Archive"],
        ),
    ]

    # Inclusion: only 4k
    inc = engine.filter_inventory(items, InventoryFilter(tags=["4k"]))
    assert len(inc) == 1
    assert inc[0].id == "1"

    # Exclusion: exclude Archive
    exc = engine.filter_inventory(items, InventoryFilter(not_tags=["archive"]))
    assert len(exc) == 1
    assert exc[0].id == "1"
```

---

### 19. `tests/test_cli_scan.py` (test, request-response)

**Analog:** `tests/test_cli_scan.py:14-80`

**CLI Scan Filter Flags Test Pattern**:
```python
@respx.mock
def test_cli_scan_negative_language_and_title_filter(tmp_path: Path, sample_valid_yaml: str):
    """Verify CLI scan flags `--!l` and `--title` correctly filter output."""
    cfg = tmp_path / "config.yaml"
    cfg.write_text(sample_valid_yaml, encoding="utf-8")

    respx.get("http://localhost:7878/api/v3/movie").respond(
        json=[
            {
                "id": 1,
                "title": "The Matrix",
                "year": 1999,
                "path": "/movies/The Matrix (1999)",
                "monitored": True,
                "hasFile": True,
                "tags": [1],
            }
        ]
    )
    respx.get("http://localhost:7878/api/v3/moviefile").respond(
        json=[
            {
                "id": 101,
                "movieId": 1,
                "relativePath": "The Matrix (1999).mkv",
                "path": "/movies/The Matrix (1999)/The Matrix (1999).mkv",
                "size": 15_000_000_000,
                "dateAdded": "2023-01-01T00:00:00Z",
                "mediaInfo": {"audioLanguages": "Japanese"},
            }
        ]
    )
    respx.get("http://localhost:7878/api/v3/tag").respond(
        json=[{"id": 1, "label": "4k"}]
    )
    respx.get("http://localhost:7878/api/v3/history").respond(
        json={"page": 1, "pageSize": 1000, "totalRecords": 0, "records": []}
    )

    # 1. Negative language excludes Japanese
    res = runner.invoke(app, ["--config", str(cfg), "scan", "--!l", "ja"])
    assert res.exit_code == 0
    assert "No media items matched" in res.stdout or "Total: 0 items" in res.stdout

    # 2. Title matching matches matrix
    res2 = runner.invoke(app, ["--config", str(cfg), "scan", "--title", "matrix"])
    assert res2.exit_code == 0
    assert "The Matrix" in res2.stdout

    # 3. Tag filtering matches 4k
    res3 = runner.invoke(app, ["--config", str(cfg), "scan", "--tag", "4k"])
    assert res3.exit_code == 0
    assert "The Matrix" in res3.stdout
```

---

### 20. `tests/test_cli_clean.py` (test, request-response)

**Analog:** `tests/test_cli_clean.py:15-80`

**CLI Clean Targeted Filter Execution Test Pattern**:
```python
@respx.mock
def test_cli_clean_with_negative_language_and_tag_flags(tmp_path: Path, sample_valid_yaml: str):
    """Verify clean command incorporates --!l, --title, --tag, and --!tag into dry-run action plans."""
    cfg = tmp_path / "config.yaml"
    cfg.write_text(sample_valid_yaml, encoding="utf-8")

    respx.get("http://localhost:7878/api/v3/movie").respond(
        json=[
            {
                "id": 1,
                "title": "The Matrix",
                "year": 1999,
                "path": "/movies/The Matrix (1999)",
                "monitored": True,
                "hasFile": True,
                "tags": [1],
            }
        ]
    )
    respx.get("http://localhost:7878/api/v3/moviefile").respond(
        json=[
            {
                "id": 101,
                "movieId": 1,
                "relativePath": "The Matrix (1999).mkv",
                "path": "/movies/The Matrix (1999)/The Matrix (1999).mkv",
                "size": 15_000_000_000,
                "dateAdded": "2023-01-01T00:00:00Z",
                "mediaInfo": {"audioLanguages": "English"},
            }
        ]
    )
    respx.get("http://localhost:7878/api/v3/tag").respond(
        json=[{"id": 1, "label": "4k"}]
    )
    respx.get("http://localhost:7878/api/v3/history").respond(
        json={"page": 1, "pageSize": 1000, "totalRecords": 0, "records": []}
    )

    res = runner.invoke(
        app,
        [
            "--config",
            str(cfg),
            "clean",
            "--delete",
            "--title",
            "matrix",
            "--tag",
            "4k",
            "--!tag",
            "archive",
            "--!l",
            "pt-br",
        ],
    )
    assert res.exit_code == 0
    assert "Planned Actions" in res.stdout
    assert "The Matrix" in res.stdout
```
