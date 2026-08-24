"""Unit and integration tests for RadarrClient endpoints and history pagination."""

import httpx
import pytest
import respx
from pydantic import SecretStr

from arr_oldies.api.radarr import RadarrClient
from arr_oldies.models import InstanceConfig, InstanceType


@pytest.fixture
def radarr_instance() -> InstanceConfig:
    return InstanceConfig(
        name="radarr-main",
        type=InstanceType.RADARR,
        url="http://radarr.local:7878",
        api_key=SecretStr("radarrsecretkey123"),
    )


@pytest.mark.asyncio
@respx.mock
async def test_radarr_get_movies(radarr_instance: InstanceConfig):
    """Verify get_movies parses movie library entries."""
    respx.get("http://radarr.local:7878/api/v3/movie").respond(
        json=[
            {
                "id": 1,
                "title": "Interstellar",
                "year": 2014,
                "path": "/movies/Interstellar (2014)",
                "monitored": True,
                "hasFile": True,
                "movieFileId": 10,
                "movieFile": {
                    "id": 10,
                    "movieId": 1,
                    "relativePath": "Interstellar (2014).mkv",
                    "path": "/movies/Interstellar (2014)/Interstellar (2014).mkv",
                    "size": 20000000000,
                    "dateAdded": "2024-01-01T12:00:00Z",
                    "mediaInfo": {
                        "audioCodec": "DTS-HD MA",
                        "audioChannels": 5.1,
                        "audioLanguages": "eng",
                    },
                },
            }
        ]
    )

    async with RadarrClient(radarr_instance) as client:
        movies = await client.get_movies()
        assert len(movies) == 1
        assert movies[0].title == "Interstellar"
        assert movies[0].movie_file is not None
        assert movies[0].movie_file.media_info is not None
        assert movies[0].movie_file.media_info.audio_codec == "DTS-HD MA"


@pytest.mark.asyncio
@respx.mock
async def test_radarr_get_movie_by_id(radarr_instance: InstanceConfig):
    """Verify get_movie retrieves a single movie."""
    respx.get("http://radarr.local:7878/api/v3/movie/42").respond(
        json={
            "id": 42,
            "title": "The Matrix",
            "year": 1999,
            "path": "/movies/The Matrix (1999)",
            "monitored": True,
            "hasFile": False,
        }
    )

    async with RadarrClient(radarr_instance) as client:
        movie = await client.get_movie(42)
        assert movie.id == 42
        assert movie.title == "The Matrix"
        assert movie.has_file is False


@pytest.mark.asyncio
@respx.mock
async def test_radarr_get_movie_files(radarr_instance: InstanceConfig):
    """Verify get_movie_files with movieId filter."""
    respx.get("http://radarr.local:7878/api/v3/moviefile", params={"movieId": 42}).respond(
        json=[
            {
                "id": 100,
                "movieId": 42,
                "relativePath": "The Matrix (1999).mkv",
                "path": "/movies/The Matrix (1999)/The Matrix (1999).mkv",
                "size": 8000000000,
                "dateAdded": "2024-01-02T15:00:00Z",
            }
        ]
    )

    async with RadarrClient(radarr_instance) as client:
        files = await client.get_movie_files(movie_id=42)
        assert len(files) == 1
        assert files[0].id == 100
        assert files[0].movie_id == 42


@pytest.mark.asyncio
@respx.mock
async def test_radarr_get_movie_history(radarr_instance: InstanceConfig):
    """Verify get_movie_history for a specific movie."""
    respx.get("http://radarr.local:7878/api/v3/history/movie", params={"movieId": 42}).respond(
        json=[
            {
                "id": 999,
                "movieId": 42,
                "sourceTitle": "The.Matrix.1999.1080p.BluRay",
                "eventType": "downloadFolderImported",
                "date": "2024-01-02T15:05:00Z",
                "data": {"fileId": "100"},
            }
        ]
    )

    async with RadarrClient(radarr_instance) as client:
        history = await client.get_movie_history(movie_id=42)
        assert len(history) == 1
        assert history[0].id == 999
        assert history[0].event_type == "downloadFolderImported"


@pytest.mark.asyncio
@respx.mock
async def test_radarr_batch_history_pagination(radarr_instance: InstanceConfig):
    """Verify multi-page batch history pagination and progress callbacks."""

    # Side-effect function to return page 1 or page 2 based on query params
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
                            "movieId": 10,
                            "sourceTitle": "Movie 1",
                            "eventType": "downloadFolderImported",
                            "date": "2024-01-01T00:00:00Z",
                        },
                        {
                            "id": 2,
                            "movieId": 20,
                            "sourceTitle": "Movie 2",
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
                            "movieId": 30,
                            "sourceTitle": "Movie 3",
                            "eventType": "downloadFolderImported",
                            "date": "2024-01-03T00:00:00Z",
                        }
                    ],
                },
            )
        return httpx.Response(404)

    respx.get("http://radarr.local:7878/api/v3/history").mock(side_effect=history_side_effect)

    progress_reports: list[tuple[int, int, int, int]] = []

    def on_progress(page: int, total_pages: int, total_records: int, fetched: int) -> None:
        progress_reports.append((page, total_pages, total_records, fetched))

    async with RadarrClient(radarr_instance) as client:
        records = await client.fetch_all_history(
            page_size=2,
            progress_callback=on_progress,
        )
        assert len(records) == 3
        assert [r.id for r in records] == [1, 2, 3]
        assert progress_reports == [(1, 2, 3, 2), (2, 2, 3, 3)]


@pytest.mark.asyncio
@respx.mock
async def test_radarr_iter_history_max_pages(radarr_instance: InstanceConfig):
    """Verify iter_history stops at max_pages limit."""
    respx.get("http://radarr.local:7878/api/v3/history").respond(
        json={
            "page": 1,
            "pageSize": 1,
            "totalRecords": 50,
            "records": [
                {
                    "id": 1,
                    "movieId": 10,
                    "sourceTitle": "Movie 1",
                    "eventType": "downloadFolderImported",
                    "date": "2024-01-01T00:00:00Z",
                }
            ],
        }
    )

    async with RadarrClient(radarr_instance) as client:
        records: list = []
        async for rec in client.iter_history(page_size=1, max_pages=1):
            records.append(rec)
        assert len(records) == 1
