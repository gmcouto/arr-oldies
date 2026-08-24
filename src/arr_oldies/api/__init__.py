"""Async API clients, models, and multi-instance fetcher for Radarr and Sonarr instances."""

from arr_oldies.api.base import BaseArrClient
from arr_oldies.api.factory import create_client
from arr_oldies.api.fetcher import (
    InstanceFetchResult,
    InstanceMediaData,
    MultiInstanceFetcher,
)
from arr_oldies.api.models import (
    ApiBaseModel,
    MediaInfo,
    RadarrHistoryPage,
    RadarrHistoryRecord,
    RadarrMovie,
    RadarrMovieFile,
    SonarrEpisode,
    SonarrEpisodeFile,
    SonarrHistoryPage,
    SonarrHistoryRecord,
    SonarrSeason,
    SonarrSeries,
)
from arr_oldies.api.radarr import RadarrClient
from arr_oldies.api.sonarr import SonarrClient

__all__ = [
    "ApiBaseModel",
    "BaseArrClient",
    "InstanceFetchResult",
    "InstanceMediaData",
    "MediaInfo",
    "MultiInstanceFetcher",
    "RadarrClient",
    "RadarrHistoryPage",
    "RadarrHistoryRecord",
    "RadarrMovie",
    "RadarrMovieFile",
    "SonarrClient",
    "SonarrEpisode",
    "SonarrEpisodeFile",
    "SonarrHistoryPage",
    "SonarrHistoryRecord",
    "SonarrSeason",
    "SonarrSeries",
    "create_client",
]
