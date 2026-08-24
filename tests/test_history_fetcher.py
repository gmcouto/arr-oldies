"""Integration tests for create_client factory and MultiInstanceFetcher with error isolation."""

import pytest
import respx
from pydantic import SecretStr

from arr_oldies.api.factory import create_client
from arr_oldies.api.fetcher import MultiInstanceFetcher
from arr_oldies.api.radarr import RadarrClient
from arr_oldies.api.sonarr import SonarrClient
from arr_oldies.models import InstanceConfig, InstanceType


@pytest.fixture
def radarr_inst() -> InstanceConfig:
    return InstanceConfig(
        name="radarr-hd",
        type=InstanceType.RADARR,
        url="http://radarr-hd.local:7878",
        api_key=SecretStr("radarrkey1"),
    )


@pytest.fixture
def sonarr_inst() -> InstanceConfig:
    return InstanceConfig(
        name="sonarr-anime",
        type=InstanceType.SONARR,
        url="http://sonarr-anime.local:8989",
        api_key=SecretStr("sonarrkey1"),
    )


def test_create_client_factory(radarr_inst: InstanceConfig, sonarr_inst: InstanceConfig):
    """Verify create_client instantiates typed clients based on InstanceConfig.type."""
    radarr_client = create_client(radarr_inst)
    assert isinstance(radarr_client, RadarrClient)
    assert radarr_client.instance.name == "radarr-hd"

    sonarr_client = create_client(sonarr_inst)
    assert isinstance(sonarr_client, SonarrClient)
    assert sonarr_client.instance.name == "sonarr-anime"


@pytest.mark.asyncio
@respx.mock
async def test_fetch_instance_data_radarr(radarr_inst: InstanceConfig):
    """Verify fetch_instance_data aggregates Radarr movies, movie files, and history."""
    respx.get("http://radarr-hd.local:7878/api/v3/movie").respond(
        json=[
            {
                "id": 1,
                "title": "Movie 1",
                "year": 2020,
                "path": "/movies/Movie 1 (2020)",
                "monitored": True,
                "hasFile": True,
            }
        ]
    )
    respx.get("http://radarr-hd.local:7878/api/v3/moviefile").respond(
        json=[
            {
                "id": 10,
                "movieId": 1,
                "relativePath": "Movie 1 (2020).mkv",
                "path": "/movies/Movie 1 (2020)/Movie 1 (2020).mkv",
                "size": 5000000000,
                "dateAdded": "2024-01-01T00:00:00Z",
            }
        ]
    )
    respx.get("http://radarr-hd.local:7878/api/v3/history").respond(
        json={
            "page": 1,
            "pageSize": 1000,
            "totalRecords": 1,
            "records": [
                {
                    "id": 100,
                    "movieId": 1,
                    "sourceTitle": "Movie.1.2020",
                    "eventType": "downloadFolderImported",
                    "date": "2024-01-01T01:00:00Z",
                }
            ],
        }
    )

    fetcher = MultiInstanceFetcher()
    result = await fetcher.fetch_instance_data(radarr_inst)
    assert result.success is True
    assert result.instance_name == "radarr-hd"
    assert result.instance_type == InstanceType.RADARR
    assert result.data is not None
    assert len(result.data.movies) == 1
    assert len(result.data.movie_files) == 1
    assert len(result.data.history_records) == 1
    assert result.item_count == 1
    assert result.latency_ms >= 0


@pytest.mark.asyncio
@respx.mock
async def test_fetch_instance_data_sonarr(sonarr_inst: InstanceConfig):
    """Verify fetch_instance_data aggregates Sonarr series, episode files, and history."""
    respx.get("http://sonarr-anime.local:8989/api/v3/series").respond(
        json=[
            {
                "id": 5,
                "title": "Anime 1",
                "year": 2021,
                "path": "/anime/Anime 1",
                "monitored": True,
                "seasons": [],
            }
        ]
    )
    respx.get("http://sonarr-anime.local:8989/api/v3/episodefile").respond(
        json=[
            {
                "id": 50,
                "seriesId": 5,
                "seasonNumber": 1,
                "relativePath": "S01E01.mkv",
                "path": "/anime/Anime 1/S01E01.mkv",
                "size": 1500000000,
                "dateAdded": "2024-01-05T00:00:00Z",
            }
        ]
    )
    respx.get("http://sonarr-anime.local:8989/api/v3/history").respond(
        json={
            "page": 1,
            "pageSize": 1000,
            "totalRecords": 1,
            "records": [
                {
                    "id": 500,
                    "seriesId": 5,
                    "episodeId": 501,
                    "sourceTitle": "Anime.1.S01E01",
                    "eventType": "downloadFolderImported",
                    "date": "2024-01-05T01:00:00Z",
                }
            ],
        }
    )

    fetcher = MultiInstanceFetcher()
    result = await fetcher.fetch_instance_data(sonarr_inst)
    assert result.success is True
    assert result.instance_name == "sonarr-anime"
    assert result.instance_type == InstanceType.SONARR
    assert result.data is not None
    assert len(result.data.series) == 1
    assert len(result.data.episode_files) == 1
    assert len(result.data.history_records) == 1


@pytest.mark.asyncio
@respx.mock
async def test_fetch_all_instances_data_concurrency_and_error_isolation(
    radarr_inst: InstanceConfig, sonarr_inst: InstanceConfig
):
    """Verify concurrent multi-instance fetching where one instance fails without affecting healthy instances."""
    # radarr-hd succeeds
    respx.get("http://radarr-hd.local:7878/api/v3/movie").respond(
        json=[
            {
                "id": 1,
                "title": "Movie 1",
                "year": 2020,
                "path": "/m/1",
                "monitored": True,
                "hasFile": False,
            }
        ]
    )
    respx.get("http://radarr-hd.local:7878/api/v3/moviefile").respond(json=[])
    respx.get("http://radarr-hd.local:7878/api/v3/history").respond(
        json={"page": 1, "pageSize": 1000, "totalRecords": 0, "records": []}
    )

    # sonarr-anime fails with 401 Unauthorized
    respx.get("http://sonarr-anime.local:8989/api/v3/series").respond(
        status_code=401, text="Unauthorized API Key"
    )

    progress_events: list[tuple[str, int, int, int, int]] = []

    def on_progress(
        inst_name: str, page: int, total_pages: int, total_records: int, fetched: int
    ) -> None:
        progress_events.append((inst_name, page, total_pages, total_records, fetched))

    fetcher = MultiInstanceFetcher()
    results = await fetcher.fetch_all_instances_data(
        [radarr_inst, sonarr_inst],
        progress_callback=on_progress,
    )

    assert len(results) == 2

    # Map by name
    res_map = {r.instance_name: r for r in results}

    radarr_res = res_map["radarr-hd"]
    assert radarr_res.success is True
    assert radarr_res.data is not None
    assert len(radarr_res.data.movies) == 1

    sonarr_res = res_map["sonarr-anime"]
    assert sonarr_res.success is False
    assert sonarr_res.data is None
    assert "Authentication failed (401)" in sonarr_res.error_message


@pytest.mark.asyncio
async def test_fetch_all_instances_data_empty():
    """Verify empty instance list returns empty result list."""
    fetcher = MultiInstanceFetcher()
    results = await fetcher.fetch_all_instances_data([])
    assert results == []
