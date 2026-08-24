"""Unit tests for RadarrClient mutation API endpoints (delete, unmonitor, remove)."""

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
async def test_radarr_delete_movie_file(radarr_instance: InstanceConfig) -> None:
    """Verify delete_movie_file sends DELETE request to /api/v3/moviefile/{id}."""
    route = respx.delete("http://radarr.local:7878/api/v3/moviefile/100").respond(status_code=200)

    async with RadarrClient(radarr_instance) as client:
        success = await client.delete_movie_file(100)
        assert success is True
        assert route.called


@pytest.mark.asyncio
@respx.mock
async def test_radarr_unmonitor_movie(radarr_instance: InstanceConfig) -> None:
    """Verify unmonitor_movie sends PUT request to /api/v3/movie/editor with correct payload."""
    route = respx.put("http://radarr.local:7878/api/v3/movie/editor").respond(status_code=202)

    async with RadarrClient(radarr_instance) as client:
        success = await client.unmonitor_movie(42)
        assert success is True
        assert route.called
        sent_json = route.calls.last.request.content
        import json

        parsed = json.loads(sent_json)
        assert parsed == {"movieIds": [42], "monitored": False}


@pytest.mark.asyncio
@respx.mock
async def test_radarr_delete_movie(radarr_instance: InstanceConfig) -> None:
    """Verify delete_movie sends DELETE request to /api/v3/movie/{id} with query parameters."""
    route = respx.delete(
        "http://radarr.local:7878/api/v3/movie/42",
        params={"deleteFiles": "true", "addImportExclusion": "false"},
    ).respond(status_code=200)

    async with RadarrClient(radarr_instance) as client:
        success = await client.delete_movie(42, delete_files=True, add_exclusion=False)
        assert success is True
        assert route.called
