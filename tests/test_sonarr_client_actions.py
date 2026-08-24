"""Unit tests for SonarrClient mutation API endpoints (delete, unmonitor series/episodes, remove)."""

import json

import pytest
import respx
from pydantic import SecretStr

from arr_oldies.api.sonarr import SonarrClient
from arr_oldies.models import InstanceConfig, InstanceType


@pytest.fixture
def sonarr_instance() -> InstanceConfig:
    return InstanceConfig(
        name="sonarr-main",
        type=InstanceType.SONARR,
        url="http://sonarr.local:8989",
        api_key=SecretStr("sonarrsecretkey456"),
    )


@pytest.mark.asyncio
@respx.mock
async def test_sonarr_delete_episode_file(sonarr_instance: InstanceConfig) -> None:
    """Verify delete_episode_file sends DELETE request to /api/v3/episodefile/{id}."""
    route = respx.delete("http://sonarr.local:8989/api/v3/episodefile/501").respond(status_code=204)

    async with SonarrClient(sonarr_instance) as client:
        success = await client.delete_episode_file(501)
        assert success is True
        assert route.called


@pytest.mark.asyncio
@respx.mock
async def test_sonarr_unmonitor_series(sonarr_instance: InstanceConfig) -> None:
    """Verify unmonitor_series sends PUT request to /api/v3/series/editor with correct payload."""
    route = respx.put("http://sonarr.local:8989/api/v3/series/editor").respond(status_code=202)

    async with SonarrClient(sonarr_instance) as client:
        success = await client.unmonitor_series(20)
        assert success is True
        assert route.called
        parsed = json.loads(route.calls.last.request.content)
        assert parsed == {"seriesIds": [20], "monitored": False}


@pytest.mark.asyncio
@respx.mock
async def test_sonarr_unmonitor_episodes(sonarr_instance: InstanceConfig) -> None:
    """Verify unmonitor_episodes sends PUT request to /api/v3/episode/monitor with correct payload."""
    route = respx.put("http://sonarr.local:8989/api/v3/episode/monitor").respond(status_code=200)

    async with SonarrClient(sonarr_instance) as client:
        success = await client.unmonitor_episodes([101, 102, 103])
        assert success is True
        assert route.called
        parsed = json.loads(route.calls.last.request.content)
        assert parsed == {"episodeIds": [101, 102, 103], "monitored": False}


@pytest.mark.asyncio
@respx.mock
async def test_sonarr_delete_series(sonarr_instance: InstanceConfig) -> None:
    """Verify delete_series sends DELETE request to /api/v3/series/{id} with query parameters."""
    route = respx.delete(
        "http://sonarr.local:8989/api/v3/series/20",
        params={"deleteFiles": "false", "addImportListExclusion": "true"},
    ).respond(status_code=200)

    async with SonarrClient(sonarr_instance) as client:
        success = await client.delete_series(20, delete_files=False, add_exclusion=True)
        assert success is True
        assert route.called
