"""Pydantic v2 data models for unified media inventory, filter options, and summaries."""

from datetime import UTC, datetime
from enum import StrEnum

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
    monitored: bool = True
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
            return v.replace(tzinfo=UTC)
        return v.astimezone(UTC)


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
    monitored_only: bool = False
    unmonitored_only: bool = False


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
