"""Multi-instance resilient fetcher for concurrent library and history acquisition."""

import asyncio
import time
from collections.abc import Callable
from typing import Any

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
)
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
    history_records: list[RadarrHistoryRecord | SonarrHistoryRecord] = Field(default_factory=list)


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

        def _history_progress(page: int, total_pages: int, total_records: int, fetched: int) -> None:
            if progress_callback is not None:
                progress_callback(instance.name, page, total_pages, total_records, fetched)

        try:
            client = create_client(instance)
            async with client:
                if instance.type == InstanceType.RADARR:
                    movies = await client.get_movies()  # type: ignore[union-attr]
                    movie_files = await client.get_movie_files()  # type: ignore[union-attr]
                    history = await client.fetch_all_history(  # type: ignore[union-attr]
                        page_size=history_page_size,
                        progress_callback=_history_progress,
                    )
                    data = InstanceMediaData(
                        instance_name=instance.name,
                        instance_type=instance.type,
                        movies=movies,
                        movie_files=movie_files,
                        history_records=history,
                    )
                    item_count = len(movie_files) or len(movies)

                elif instance.type == InstanceType.SONARR:
                    series = await client.get_series()  # type: ignore[union-attr]
                    episode_files = await client.get_all_episode_files()  # type: ignore[union-attr]
                    history = await client.fetch_all_history(  # type: ignore[union-attr]
                        page_size=history_page_size,
                        progress_callback=_history_progress,
                    )
                    data = InstanceMediaData(
                        instance_name=instance.name,
                        instance_type=instance.type,
                        series=series,
                        episode_files=episode_files,
                        history_records=history,
                    )
                    item_count = len(episode_files) or len(series)
                else:
                    raise ValueError(f"Unknown instance type '{instance.type}'")

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
        except Exception as exc:
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
        """Fetch media library and history records across all instances concurrently."""
        if not instances:
            return []

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
            if isinstance(result, Exception):
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
