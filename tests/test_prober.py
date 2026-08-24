"""Unit tests for async HTTPX health prober with respx mocking."""

import httpx
import pytest
import respx

from arr_oldies.models import InstanceConfig, InstanceType
from arr_oldies.prober import probe_all_instances, probe_single_instance


@pytest.fixture
def radarr_instance() -> InstanceConfig:
    """Create a sample Radarr InstanceConfig."""
    return InstanceConfig(
        name="radarr-main",
        type=InstanceType.RADARR,
        url="http://localhost:7878",
        api_key="valid_api_key_123",  # type: ignore[arg-type]
        timeout=10.0,
    )


@pytest.fixture
def sonarr_instance() -> InstanceConfig:
    """Create a sample Sonarr InstanceConfig."""
    return InstanceConfig(
        name="sonarr-tv",
        type=InstanceType.SONARR,
        url="https://sonarr.local:8989",
        api_key="sonarr_api_key_456",  # type: ignore[arg-type]
        timeout=5.0,
    )


@respx.mock
async def test_probe_single_instance_success(radarr_instance: InstanceConfig) -> None:
    """Verify HTTP 200 returns successful ProbeResult with version and latency."""
    respx.get("http://localhost:7878/api/v3/system/status").respond(
        status_code=200,
        json={"version": "5.3.6.8777", "instanceName": "Radarr-Main"},
    )

    result = await probe_single_instance(radarr_instance)
    assert result.success is True
    assert result.instance_name == "radarr-main"
    assert result.instance_type == InstanceType.RADARR
    assert result.version == "5.3.6.8777"
    assert result.latency_ms > 0.0
    assert result.error_message is None


@respx.mock
async def test_probe_single_instance_unauthorized(radarr_instance: InstanceConfig) -> None:
    """Verify HTTP 401 returns unauthorized failure message without raising unhandled error."""
    respx.get("http://localhost:7878/api/v3/system/status").respond(status_code=401)

    result = await probe_single_instance(radarr_instance)
    assert result.success is False
    assert result.error_message is not None
    assert "401 Unauthorized" in result.error_message


@respx.mock
async def test_probe_single_instance_not_found(radarr_instance: InstanceConfig) -> None:
    """Verify HTTP 404 returns not found failure message."""
    respx.get("http://localhost:7878/api/v3/system/status").respond(status_code=404)

    result = await probe_single_instance(radarr_instance)
    assert result.success is False
    assert result.error_message is not None
    assert "404 Not Found" in result.error_message


@respx.mock
async def test_probe_single_instance_connect_error(radarr_instance: InstanceConfig) -> None:
    """Verify connection error is caught and translated to user-friendly message."""
    respx.get("http://localhost:7878/api/v3/system/status").mock(
        side_effect=httpx.ConnectError("Connection refused")
    )

    result = await probe_single_instance(radarr_instance)
    assert result.success is False
    assert result.error_message == "Connection refused / Host unreachable"


@respx.mock
async def test_probe_single_instance_timeout_error(radarr_instance: InstanceConfig) -> None:
    """Verify timeout is caught and translated to user-friendly message."""
    respx.get("http://localhost:7878/api/v3/system/status").mock(
        side_effect=httpx.TimeoutException("Read timed out")
    )

    result = await probe_single_instance(radarr_instance)
    assert result.success is False
    assert result.error_message is not None
    assert "Connection timed out" in result.error_message


@respx.mock
async def test_probe_all_instances_concurrent(
    radarr_instance: InstanceConfig, sonarr_instance: InstanceConfig
) -> None:
    """Verify probe_all_instances probes multiple instances concurrently."""
    respx.get("http://localhost:7878/api/v3/system/status").respond(
        status_code=200, json={"version": "5.3.6"}
    )
    respx.get("https://sonarr.local:8989/api/v3/system/status").respond(status_code=401)

    results = await probe_all_instances([radarr_instance, sonarr_instance])
    assert len(results) == 2

    assert results[0].instance_name == "radarr-main"
    assert results[0].success is True
    assert results[0].version == "5.3.6"

    assert results[1].instance_name == "sonarr-tv"
    assert results[1].success is False
    assert results[1].error_message is not None
    assert "401 Unauthorized" in results[1].error_message
