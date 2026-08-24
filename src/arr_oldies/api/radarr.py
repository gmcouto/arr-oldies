"""Radarr async REST API client and history pagination engine."""

import math
from collections.abc import AsyncIterator, Callable
from typing import Any

from arr_oldies.api.base import BaseArrClient
from arr_oldies.api.models import (
    RadarrHistoryPage,
    RadarrHistoryRecord,
    RadarrMovie,
    RadarrMovieFile,
)
from arr_oldies.constants import (
    DEFAULT_HISTORY_PAGE_SIZE,
    RADARR_HISTORY_ENDPOINT,
    RADARR_HISTORY_MOVIE_ENDPOINT,
    RADARR_MOVIE_ENDPOINT,
    RADARR_MOVIEFILE_ENDPOINT,
)


class RadarrClient(BaseArrClient):
    """Async API client for Radarr v3/v4 instances."""

    async def get_movies(self) -> list[RadarrMovie]:
        """Retrieve all movies in the Radarr library."""
        response = await self.get(RADARR_MOVIE_ENDPOINT)
        data = response.json()
        return [RadarrMovie.model_validate(item) for item in data]

    async def get_movie(self, movie_id: int) -> RadarrMovie:
        """Retrieve a single movie by ID."""
        response = await self.get(f"{RADARR_MOVIE_ENDPOINT}/{movie_id}")
        return RadarrMovie.model_validate(response.json())

    async def get_movie_files(self, movie_id: int | None = None) -> list[RadarrMovieFile]:
        """Retrieve movie file records, optionally filtered by movie ID."""
        params: dict[str, Any] = {}
        if movie_id is not None:
            params["movieId"] = movie_id
        response = await self.get(RADARR_MOVIEFILE_ENDPOINT, params=params if params else None)
        data = response.json()
        if isinstance(data, dict):
            return [RadarrMovieFile.model_validate(data)]
        return [RadarrMovieFile.model_validate(item) for item in data]

    async def get_history(
        self,
        page: int = 1,
        page_size: int = DEFAULT_HISTORY_PAGE_SIZE,
        sort_key: str = "date",
        sort_dir: str = "descending",
        event_type: int | str | None = None,
    ) -> RadarrHistoryPage:
        """Query a single paginated page of Radarr history events."""
        params: dict[str, Any] = {
            "page": page,
            "pageSize": page_size,
            "sortKey": sort_key,
            "sortDirection": sort_dir,
        }
        if event_type is not None:
            params["eventType"] = event_type
        response = await self.get(RADARR_HISTORY_ENDPOINT, params=params)
        return RadarrHistoryPage.model_validate(response.json())

    async def get_movie_history(
        self,
        movie_id: int,
        event_type: int | str | None = None,
    ) -> list[RadarrHistoryRecord]:
        """Retrieve full history event records for a specific movie."""
        params: dict[str, Any] = {"movieId": movie_id}
        if event_type is not None:
            params["eventType"] = event_type
        response = await self.get(RADARR_HISTORY_MOVIE_ENDPOINT, params=params)
        data = response.json()
        return [RadarrHistoryRecord.model_validate(item) for item in data]

    async def iter_history(
        self,
        page_size: int = DEFAULT_HISTORY_PAGE_SIZE,
        max_pages: int | None = None,
        event_type: int | str | None = None,
    ) -> AsyncIterator[RadarrHistoryRecord]:
        """Asynchronously iterate through history records page-by-page."""
        page_num = 1
        while True:
            if max_pages is not None and page_num > max_pages:
                break

            history_page = await self.get_history(
                page=page_num,
                page_size=page_size,
                event_type=event_type,
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
        progress_callback: Callable[[int, int, int, int], None] | None = None,
    ) -> list[RadarrHistoryRecord]:
        """Fetch and aggregate all history records sequentially with progress reporting."""
        records: list[RadarrHistoryRecord] = []
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
            )

            if total_records is None:
                total_records = history_page.total_records
                total_pages = (
                    max(1, math.ceil(total_records / page_size)) if total_records > 0 else 1
                )

            if not history_page.records:
                break

            records.extend(history_page.records)

            if progress_callback is not None:
                progress_callback(page_num, total_pages, total_records, len(records))

            if page_num * page_size >= history_page.total_records:
                break

            page_num += 1

        return records

    async def delete_movie_file(self, movie_file_id: int) -> bool:
        """Delete a specific movie file from disk and database."""
        endpoint = f"{RADARR_MOVIEFILE_ENDPOINT}/{movie_file_id}"
        response = await self.delete(endpoint)
        return response.status_code in (200, 204)

    async def unmonitor_movie(self, movie_id: int) -> bool:
        """Unmonitor a movie to prevent automatic redownload."""
        endpoint = f"{RADARR_MOVIE_ENDPOINT}/editor"
        payload = {"movieIds": [movie_id], "monitored": False}
        response = await self.put(endpoint, json=payload)
        return response.status_code in (200, 202)

    async def delete_movie(
        self,
        movie_id: int,
        delete_files: bool = False,
        add_exclusion: bool = False,
    ) -> bool:
        """Delete a movie entry from library, optionally deleting files and adding import exclusion."""
        endpoint = f"{RADARR_MOVIE_ENDPOINT}/{movie_id}"
        params = {
            "deleteFiles": str(delete_files).lower(),
            "addImportExclusion": str(add_exclusion).lower(),
        }
        response = await self.delete(endpoint, params=params)
        return response.status_code in (200, 204)
