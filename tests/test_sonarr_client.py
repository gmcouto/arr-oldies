"""Unit and integration tests for SonarrClient endpoints, throttling, and history pagination."""

import httpx
import pytest
import respx
from pydantic import SecretStr

from arr_oldies.api.sonarr import SonarrClient
from arr_oldies.models import InstanceConfig, InstanceType


@pytest.fixture
def sonarr_instance() -> InstanceConfig:
    return InstanceConfig(
        name="sonarr-tv",
        type=InstanceType.SONARR,
        url="http://sonarr.local:8989",
        api_key=SecretStr("sonarrsecretkey123"),
    )


@pytest.mark.asyncio
@respx.mock
async def test_sonarr_get_series(sonarr_instance: InstanceConfig):
    """Verify get_series and get_series_by_id parsing."""
    respx.get("http://sonarr.local:8989/api/v3/series").respond(
        json=[
            {
                "id": 10,
                "title": "Better Call Saul",
                "year": 2015,
                "path": "/tv/Better Call Saul",
                "monitored": True,
                "seasons": [
                    {
                        "seasonNumber": 1,
                        "monitored": True,
                        "statistics": {"episodeFileCount": 10},
                    }
                ],
            }
        ]
    )
    respx.get("http://sonarr.local:8989/api/v3/series/10").respond(
        json={
            "id": 10,
            "title": "Better Call Saul",
            "year": 2015,
            "path": "/tv/Better Call Saul",
            "monitored": True,
            "seasons": [],
        }
    )

    async with SonarrClient(sonarr_instance) as client:
        series_list = await client.get_series()
        assert len(series_list) == 1
        assert series_list[0].id == 10
        assert series_list[0].title == "Better Call Saul"

        single = await client.get_series_by_id(10)
        assert single.id == 10
        assert single.title == "Better Call Saul"


@pytest.mark.asyncio
@respx.mock
async def test_sonarr_get_episode_files_and_throttled_all(sonarr_instance: InstanceConfig):
    """Verify get_episode_files and get_all_episode_files concurrency throttling."""

    def episode_file_side_effect(request: httpx.Request):
        series_id = request.url.params.get("seriesId")
        if series_id == "1":
            return httpx.Response(
                200,
                json=[
                    {
                        "id": 101,
                        "seriesId": 1,
                        "seasonNumber": 1,
                        "relativePath": "S01E01.mkv",
                        "path": "/tv/Show1/S01E01.mkv",
                        "size": 1000000,
                        "dateAdded": "2024-01-01T00:00:00Z",
                    }
                ],
            )
        elif series_id == "2":
            return httpx.Response(
                200,
                json=[
                    {
                        "id": 102,
                        "seriesId": 2,
                        "seasonNumber": 1,
                        "relativePath": "S01E01.mkv",
                        "path": "/tv/Show2/S01E01.mkv",
                        "size": 2000000,
                        "dateAdded": "2024-01-02T00:00:00Z",
                    }
                ],
            )
        return httpx.Response(200, json=[])

    respx.get("http://sonarr.local:8989/api/v3/episodefile").mock(
        side_effect=episode_file_side_effect
    )

    async with SonarrClient(sonarr_instance) as client:
        # Test single series episode file
        files_s1 = await client.get_episode_files(1)
        assert len(files_s1) == 1
        assert files_s1[0].id == 101

        # Test throttled multi-series episode file fetching
        all_files = await client.get_all_episode_files(series_ids=[1, 2], concurrency=2)
        assert len(all_files) == 2
        assert {f.id for f in all_files} == {101, 102}


@pytest.mark.asyncio
@respx.mock
async def test_sonarr_get_episodes(sonarr_instance: InstanceConfig):
    """Verify get_episodes query filtering."""
    respx.get("http://sonarr.local:8989/api/v3/episode").mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "id": 501,
                    "seriesId": 10,
                    "episodeFileId": 101,
                    "seasonNumber": 1,
                    "episodeNumber": 1,
                    "title": "Uno",
                    "monitored": True,
                    "hasFile": True,
                }
            ],
        )
    )

    async with SonarrClient(sonarr_instance) as client:
        episodes = await client.get_episodes(series_id=10)
        assert len(episodes) == 1
        assert episodes[0].id == 501
        assert episodes[0].title == "Uno"


@pytest.mark.asyncio
@respx.mock
async def test_sonarr_get_all_episodes(sonarr_instance: InstanceConfig):
    """Verify get_all_episodes retrieves episodes across multiple series."""
    respx.get("http://sonarr.local:8989/api/v3/episode", params={"seriesId": 1}).mock(
        return_value=httpx.Response(
            200,
            json=[
                {"id": 101, "seriesId": 1, "seasonNumber": 1, "episodeNumber": 1, "title": "Ep1"}
            ],
        )
    )
    respx.get("http://sonarr.local:8989/api/v3/episode", params={"seriesId": 2}).mock(
        return_value=httpx.Response(
            200,
            json=[
                {"id": 102, "seriesId": 2, "seasonNumber": 1, "episodeNumber": 2, "title": "Ep2"}
            ],
        )
    )

    async with SonarrClient(sonarr_instance) as client:
        all_eps = await client.get_all_episodes(series_ids=[1, 2], concurrency=2)
        assert len(all_eps) == 2
        assert {e.id for e in all_eps} == {101, 102}


@pytest.mark.asyncio
@respx.mock
async def test_sonarr_get_series_history(sonarr_instance: InstanceConfig):
    """Verify get_series_history for a series."""
    respx.get("http://sonarr.local:8989/api/v3/history/series").mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "id": 888,
                    "seriesId": 10,
                    "episodeId": 501,
                    "sourceTitle": "Better.Call.Saul.S01E01.1080p",
                    "eventType": "downloadFolderImported",
                    "date": "2024-01-10T12:00:00Z",
                    "data": {"fileId": "101"},
                }
            ],
        )
    )

    async with SonarrClient(sonarr_instance) as client:
        records = await client.get_series_history(series_id=10, season_number=1)
        assert len(records) == 1
        assert records[0].id == 888
        assert records[0].series_id == 10
        assert records[0].episode_id == 501


@pytest.mark.asyncio
@respx.mock
async def test_sonarr_batch_history_pagination(sonarr_instance: InstanceConfig):
    """Verify multi-page batch history pagination and progress callbacks."""

    def history_side_effect(request: httpx.Request):
        page = request.url.params.get("page")
        if page == "1":
            return httpx.Response(
                200,
                json={
                    "page": 1,
                    "pageSize": 2,
                    "totalRecords": 3,
                    "records": [
                        {
                            "id": 1,
                            "seriesId": 10,
                            "episodeId": 101,
                            "sourceTitle": "Ep 1",
                            "eventType": "downloadFolderImported",
                            "date": "2024-01-01T00:00:00Z",
                        },
                        {
                            "id": 2,
                            "seriesId": 10,
                            "episodeId": 102,
                            "sourceTitle": "Ep 2",
                            "eventType": "downloadFolderImported",
                            "date": "2024-01-02T00:00:00Z",
                        },
                    ],
                },
            )
        elif page == "2":
            return httpx.Response(
                200,
                json={
                    "page": 2,
                    "pageSize": 2,
                    "totalRecords": 3,
                    "records": [
                        {
                            "id": 3,
                            "seriesId": 10,
                            "episodeId": 103,
                            "sourceTitle": "Ep 3",
                            "eventType": "downloadFolderImported",
                            "date": "2024-01-03T00:00:00Z",
                        }
                    ],
                },
            )
        return httpx.Response(404)

    respx.get("http://sonarr.local:8989/api/v3/history").mock(side_effect=history_side_effect)

    progress_reports: list[tuple[int, int, int, int]] = []

    def on_progress(page: int, total_pages: int, total_records: int, fetched: int) -> None:
        progress_reports.append((page, total_pages, total_records, fetched))

    async with SonarrClient(sonarr_instance) as client:
        records = await client.fetch_all_history(
            page_size=2,
            progress_callback=on_progress,
        )
        assert len(records) == 3
        assert [r.id for r in records] == [1, 2, 3]
        assert progress_reports == [(1, 2, 3, 2), (2, 2, 3, 3)]
