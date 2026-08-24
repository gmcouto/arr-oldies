"""Multi-instance resilient fetcher for concurrent library and history acquisition."""

import asyncio
import time
from collections.abc import Callable

from pydantic import BaseModel, Field

from arr_oldies.api.factory import create_client
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
from arr_oldies.api.radarr import RadarrClient
from arr_oldies.api.sonarr import SonarrClient
from arr_oldies.constants import DEFAULT_HISTORY_PAGE_SIZE
from arr_oldies.exceptions import ArrClientError
from arr_oldies.models import InstanceConfig, InstanceType


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


class InstanceFetchResult(BaseModel):
    """Diagnostic wrapper containing instance fetch outcomes, timings, and payloads."""

    instance_name: str
    instance_type: InstanceType
    url: str
    success: bool
    data: InstanceMediaData | None = None
    error_message: str | None = None
    warning_message: str | None = None
    item_count: int = 0
    latency_ms: float = 0.0


class MultiInstanceFetcher:
    """Orchestrates resilient, concurrent scans across multiple Radarr/Sonarr instances."""

    async def fetch_instance_data(
        self,
        instance: InstanceConfig,
        history_page_size: int = DEFAULT_HISTORY_PAGE_SIZE,
        progress_callback: Callable[[str, int, int, int, int], None] | None = None,
    ) -> InstanceFetchResult:
        """Fetch media library and history records for a single instance with error isolation."""
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

        except ArrClientError as exc:
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            return InstanceFetchResult(
                instance_name=instance.name,
                instance_type=instance.type,
                url=instance.url,
                success=False,
                error_message=str(exc),
                latency_ms=round(latency_ms, 2),
            )
        except Exception as exc:  # noqa: BLE001
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            return InstanceFetchResult(
                instance_name=instance.name,
                instance_type=instance.type,
                url=instance.url,
                success=False,
                error_message=f"Unexpected error: {exc}",
                latency_ms=round(latency_ms, 2),
            )

    async def fetch_all_instances_data(
        self,
        instances: list[InstanceConfig],
        history_page_size: int = DEFAULT_HISTORY_PAGE_SIZE,
        progress_callback: Callable[[str, int, int, int, int], None] | None = None,
    ) -> list[InstanceFetchResult]:
        """Fetch media and history records from all configured instances concurrently."""
        tasks = [
            self.fetch_instance_data(
                instance=inst,
                history_page_size=history_page_size,
                progress_callback=progress_callback,
            )
            for inst in instances
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        final_results: list[InstanceFetchResult] = []
        for i, result in enumerate(results):
            if isinstance(result, BaseException):
                inst = instances[i]
                final_results.append(
                    InstanceFetchResult(
                        instance_name=inst.name,
                        instance_type=inst.type,
                        url=inst.url,
                        success=False,
                        error_message=f"Task exception: {result}",
                    )
                )
            else:
                final_results.append(result)

        return final_results
