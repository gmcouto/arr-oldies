"""Sonarr async REST API client, throttled episode file fetcher, and history pagination."""

import asyncio
import math
from collections.abc import AsyncIterator, Callable
from typing import Any

from arr_oldies.api.base import BaseArrClient
from arr_oldies.api.models import (
    SonarrEpisode,
    SonarrEpisodeFile,
    SonarrHistoryPage,
    SonarrHistoryRecord,
    SonarrSeries,
)
from arr_oldies.constants import (
    DEFAULT_HISTORY_PAGE_SIZE,
    DEFAULT_SERIES_CONCURRENCY,
    SONARR_EPISODE_ENDPOINT,
    SONARR_EPISODEFILE_ENDPOINT,
    SONARR_HISTORY_ENDPOINT,
    SONARR_HISTORY_SERIES_ENDPOINT,
    SONARR_SERIES_ENDPOINT,
)


class SonarrClient(BaseArrClient):
    """Async API client for Sonarr v3/v4 instances."""

    async def get_series(self) -> list[SonarrSeries]:
        """Retrieve all TV series in the Sonarr library."""
        response = await self.get(SONARR_SERIES_ENDPOINT)
        data = response.json()
        return [SonarrSeries.model_validate(item) for item in data]

    async def get_series_by_id(self, series_id: int) -> SonarrSeries:
        """Retrieve a single TV series by ID."""
        response = await self.get(f"{SONARR_SERIES_ENDPOINT}/{series_id}")
        return SonarrSeries.model_validate(response.json())

    async def get_episode_files(self, series_id: int) -> list[SonarrEpisodeFile]:
        """Retrieve all episode file records for a specific series."""
        params = {"seriesId": series_id}
        response = await self.get(SONARR_EPISODEFILE_ENDPOINT, params=params)
        data = response.json()
        if isinstance(data, dict):
            return [SonarrEpisodeFile.model_validate(data)]
        return [SonarrEpisodeFile.model_validate(item) for item in data]

    async def get_all_episode_files(
        self,
        series_ids: list[int] | None = None,
        concurrency: int = DEFAULT_SERIES_CONCURRENCY,
    ) -> list[SonarrEpisodeFile]:
        """Fetch all episode files across multiple series, throttled with a semaphore."""
        if series_ids is None:
            series_list = await self.get_series()
            series_ids = [s.id for s in series_list]

        if not series_ids:
            return []

        semaphore = asyncio.Semaphore(concurrency)

        async def _fetch_for_series(sid: int) -> list[SonarrEpisodeFile]:
            async with semaphore:
                return await self.get_episode_files(sid)

        tasks = [_fetch_for_series(sid) for sid in series_ids]
        results = await asyncio.gather(*tasks)

        all_files: list[SonarrEpisodeFile] = []
        for file_list in results:
            all_files.extend(file_list)

        return all_files

    async def get_episodes(
        self,
        series_id: int | None = None,
        episode_file_id: int | None = None,
    ) -> list[SonarrEpisode]:
        """Retrieve episode metadata records."""
        params: dict[str, Any] = {}
        if series_id is not None:
            params["seriesId"] = series_id
        if episode_file_id is not None:
            params["episodeFileId"] = episode_file_id

        response = await self.get(SONARR_EPISODE_ENDPOINT, params=params if params else None)
        data = response.json()
        if isinstance(data, dict):
            return [SonarrEpisode.model_validate(data)]
        return [SonarrEpisode.model_validate(item) for item in data]

    async def get_history(
        self,
        page: int = 1,
        page_size: int = DEFAULT_HISTORY_PAGE_SIZE,
        sort_key: str = "date",
        sort_dir: str = "descending",
        event_type: int | str | None = None,
        include_series: bool = True,
        include_episode: bool = True,
    ) -> SonarrHistoryPage:
        """Query a single paginated page of Sonarr history events."""
        params: dict[str, Any] = {
            "page": page,
            "pageSize": page_size,
            "sortKey": sort_key,
            "sortDirection": sort_dir,
            "includeSeries": str(include_series).lower(),
            "includeEpisode": str(include_episode).lower(),
        }
        if event_type is not None:
            params["eventType"] = event_type
        response = await self.get(SONARR_HISTORY_ENDPOINT, params=params)
        return SonarrHistoryPage.model_validate(response.json())

    async def get_series_history(
        self,
        series_id: int,
        season_number: int | None = None,
    ) -> list[SonarrHistoryRecord]:
        """Retrieve history event records for a specific series."""
        params: dict[str, Any] = {"seriesId": series_id}
        if season_number is not None:
            params["seasonNumber"] = season_number
        response = await self.get(SONARR_HISTORY_SERIES_ENDPOINT, params=params)
        data = response.json()
        return [SonarrHistoryRecord.model_validate(item) for item in data]

    async def iter_history(
        self,
        page_size: int = DEFAULT_HISTORY_PAGE_SIZE,
        max_pages: int | None = None,
        event_type: int | str | None = None,
        include_series: bool = True,
        include_episode: bool = True,
    ) -> AsyncIterator[SonarrHistoryRecord]:
        """Asynchronously iterate through history records page-by-page."""
        page_num = 1
        while True:
            if max_pages is not None and page_num > max_pages:
                break

            history_page = await self.get_history(
                page=page_num,
                page_size=page_size,
                event_type=event_type,
                include_series=include_series,
                include_episode=include_episode,
            )

            if not history_page.records:
                break

            for record in history_page.records:
                yield record

            if page_num * page_size >= history_page.total_records:
                break

            page_num += 1

    async def fetch_all_history(
        self,
        page_size: int = DEFAULT_HISTORY_PAGE_SIZE,
        max_pages: int | None = None,
        event_type: int | str | None = None,
        include_series: bool = True,
        include_episode: bool = True,
        progress_callback: Callable[[int, int, int, int], None] | None = None,
    ) -> list[SonarrHistoryRecord]:
        """Fetch and aggregate all history records sequentially with progress reporting."""
        records: list[SonarrHistoryRecord] = []
        page_num = 1
        total_records: int | None = None
        total_pages: int = 1

        while True:
            if max_pages is not None and page_num > max_pages:
                break

            history_page = await self.get_history(
                page=page_num,
                page_size=page_size,
                event_type=event_type,
                include_series=include_series,
                include_episode=include_episode,
            )

            if total_records is None:
                total_records = history_page.total_records
                total_pages = max(1, math.ceil(total_records / page_size)) if total_records > 0 else 1

            if not history_page.records:
                break

            records.extend(history_page.records)

            if progress_callback is not None:
                progress_callback(page_num, total_pages, total_records, len(records))

            if page_num * page_size >= history_page.total_records:
                break

            page_num += 1

        return records
