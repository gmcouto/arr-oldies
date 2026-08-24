"""Pydantic v2 schemas for Radarr and Sonarr REST API responses."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ApiBaseModel(BaseModel):
    """Base model configured to ignore extra fields for API forward compatibility."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)


class Tag(ApiBaseModel):
    """Tag descriptor mapping tag ID to human-readable label."""

    id: int
    label: str


class MediaInfo(ApiBaseModel):
    """Media technical stream metadata extracted from media file."""

    audio_codec: str | None = Field(default=None, alias="audioCodec")
    audio_channels: float | None = Field(default=None, alias="audioChannels")
    audio_profile: str | None = Field(default=None, alias="audioProfile")
    audio_languages: str | None = Field(default=None, alias="audioLanguages")
    audio_title: str | None = Field(default=None, alias="audioTitle")
    video_codec: str | None = Field(default=None, alias="videoCodec")
    video_bitdepth: int | None = Field(default=None, alias="videoBitdepth")
    video_bitrate: int | None = Field(default=None, alias="videoBitrate")
    video_fps: float | None = Field(default=None, alias="videoFps")
    resolution: str | None = Field(default=None, alias="resolution")
    run_time: str | None = Field(default=None, alias="runTime")
    scan_type: str | None = Field(default=None, alias="scanType")
    subtitles: str | None = Field(default=None, alias="subtitles")


# --- Radarr Models ---


class RadarrMovieFile(ApiBaseModel):
    """Movie media file descriptor."""

    id: int
    movie_id: int = Field(alias="movieId")
    relative_path: str = Field(default="", alias="relativePath")
    path: str = Field(default="")
    size: int = Field(default=0)
    date_added: datetime = Field(alias="dateAdded")
    indexer_flags: int | None = Field(default=None, alias="indexerFlags")
    media_info: MediaInfo | None = Field(default=None, alias="mediaInfo")
    quality: dict[str, Any] | None = Field(default=None)


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


class RadarrHistoryRecord(ApiBaseModel):
    """Radarr history event record."""

    id: int
    movie_id: int = Field(alias="movieId")
    source_title: str = Field(default="", alias="sourceTitle")
    event_type: str = Field(alias="eventType")
    date: datetime
    data: dict[str, Any] = Field(default_factory=dict)
    download_id: str | None = Field(default=None, alias="downloadId")


class RadarrHistoryPage(ApiBaseModel):
    """Paginated history response from Radarr."""

    page: int
    page_size: int = Field(alias="pageSize")
    total_records: int = Field(alias="totalRecords")
    records: list[RadarrHistoryRecord] = Field(default_factory=list)


# --- Sonarr Models ---


class SonarrSeason(ApiBaseModel):
    """Sonarr series season metadata."""

    season_number: int = Field(alias="seasonNumber")
    monitored: bool = Field(default=True)
    statistics: dict[str, Any] | None = Field(default=None)


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


class SonarrEpisodeFile(ApiBaseModel):
    """Sonarr episode media file descriptor."""

    id: int
    series_id: int = Field(alias="seriesId")
    season_number: int = Field(default=0, alias="seasonNumber")
    relative_path: str = Field(default="", alias="relativePath")
    path: str = Field(default="")
    size: int = Field(default=0)
    date_added: datetime = Field(alias="dateAdded")
    media_info: MediaInfo | None = Field(default=None, alias="mediaInfo")
    quality: dict[str, Any] | None = Field(default=None)


class SonarrEpisode(ApiBaseModel):
    """Sonarr episode metadata."""

    id: int
    series_id: int = Field(alias="seriesId")
    episode_file_id: int | None = Field(default=None, alias="episodeFileId")
    season_number: int = Field(alias="seasonNumber")
    episode_number: int = Field(alias="episodeNumber")
    title: str = Field(default="")
    air_date_utc: datetime | None = Field(default=None, alias="airDateUtc")
    monitored: bool = Field(default=True)
    has_file: bool = Field(default=False, alias="hasFile")


class SonarrHistoryRecord(ApiBaseModel):
    """Sonarr history event record."""

    id: int
    series_id: int = Field(alias="seriesId")
    episode_id: int = Field(alias="episodeId")
    source_title: str = Field(default="", alias="sourceTitle")
    event_type: str = Field(alias="eventType")
    date: datetime
    data: dict[str, Any] = Field(default_factory=dict)
    download_id: str | None = Field(default=None, alias="downloadId")


class SonarrHistoryPage(ApiBaseModel):
    """Paginated history response from Sonarr."""

    page: int
    page_size: int = Field(alias="pageSize")
    total_records: int = Field(alias="totalRecords")
    records: list[SonarrHistoryRecord] = Field(default_factory=list)
