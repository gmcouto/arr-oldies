"""Unit tests for BaseArrClient HTTPX async engine, retries, and error mapping."""

import asyncio
from unittest.mock import patch

import httpx
import pytest
import respx
from pydantic import SecretStr

from arr_oldies.api.base import BaseArrClient
from arr_oldies.exceptions import (
    ArrAuthenticationError,
    ArrConnectionError,
    ArrDatabaseLockedError,
    ArrNotFoundError,
    ArrResponseError,
    ArrTimeoutError,
)
from arr_oldies.models import InstanceConfig, InstanceType


@pytest.fixture
def mock_instance() -> InstanceConfig:
    return InstanceConfig(
        name="test-radarr",
        type=InstanceType.RADARR,
        url="http://radarr.local:7878",
        api_key=SecretStr("supersecretapikey123"),
        timeout=10.0,
        verify_ssl=False,
    )


@pytest.mark.asyncio
async def test_base_client_headers_and_config(mock_instance: InstanceConfig):
    """Verify that BaseArrClient sets appropriate headers and SSL verification."""
    client = BaseArrClient(mock_instance)
    raw_client = client.client
    assert raw_client.base_url == "http://radarr.local:7878"
    assert raw_client.headers["x-api-key"] == "supersecretapikey123"
    assert "arr-oldies" in raw_client.headers["user-agent"]
    assert raw_client.headers["accept"] == "application/json"
    await client.close()


@pytest.mark.asyncio
@respx.mock
async def test_base_client_crud_methods(mock_instance: InstanceConfig):
    """Verify GET, POST, PUT, DELETE convenience methods."""
    respx.get("http://radarr.local:7878/api/v3/test").respond(json={"status": "ok"})
    respx.post("http://radarr.local:7878/api/v3/test").respond(json={"created": True}, status_code=201)
    respx.put("http://radarr.local:7878/api/v3/test").respond(json={"updated": True})
    respx.delete("http://radarr.local:7878/api/v3/test").respond(status_code=204)

    async with BaseArrClient(mock_instance) as client:
        get_res = await client.get("/api/v3/test")
        assert get_res.json() == {"status": "ok"}

        post_res = await client.post("/api/v3/test", json={"data": 1})
        assert post_res.status_code == 201
        assert post_res.json() == {"created": True}

        put_res = await client.put("/api/v3/test", json={"data": 2})
        assert put_res.json() == {"updated": True}

        del_res = await client.delete("/api/v3/test")
        assert del_res.status_code == 204


@pytest.mark.asyncio
@respx.mock
async def test_base_client_401_auth_error(mock_instance: InstanceConfig):
    """Verify HTTP 401 translates to ArrAuthenticationError without exposing the API key."""
    respx.get("http://radarr.local:7878/api/v3/secure").respond(status_code=401, text="Unauthorized")

    async with BaseArrClient(mock_instance) as client:
        with pytest.raises(ArrAuthenticationError) as exc_info:
            await client.get("/api/v3/secure")
        assert "Authentication failed" in str(exc_info.value)
        assert "supersecretapikey123" not in str(exc_info.value)


@pytest.mark.asyncio
@respx.mock
async def test_base_client_404_not_found(mock_instance: InstanceConfig):
    """Verify HTTP 404 translates to ArrNotFoundError."""
    respx.get("http://radarr.local:7878/api/v3/missing").respond(status_code=404, text="Not Found")

    async with BaseArrClient(mock_instance) as client:
        with pytest.raises(ArrNotFoundError) as exc_info:
            await client.get("/api/v3/missing")
        assert "Resource not found (404)" in str(exc_info.value)


@pytest.mark.asyncio
@respx.mock
async def test_base_client_retry_on_429_with_retry_after(mock_instance: InstanceConfig):
    """Verify 429 rate limit retries and honors Retry-After header."""
    route = respx.get("http://radarr.local:7878/api/v3/rate").mock(
        side_effect=[
            httpx.Response(429, headers={"Retry-After": "0.01"}, text="Too Many Requests"),
            httpx.Response(200, json={"success": True}),
        ]
    )

    async with BaseArrClient(mock_instance) as client:
        res = await client.get("/api/v3/rate")
        assert res.json() == {"success": True}
        assert route.call_count == 2


@pytest.mark.asyncio
@respx.mock
async def test_base_client_retry_on_503_eventual_success(mock_instance: InstanceConfig):
    """Verify 503 transient error retries and succeeds on next attempt."""
    route = respx.get("http://radarr.local:7878/api/v3/flaky").mock(
        side_effect=[
            httpx.Response(503, text="Service Unavailable"),
            httpx.Response(200, json={"recovered": True}),
        ]
    )

    with patch("asyncio.sleep", return_value=None):
        async with BaseArrClient(mock_instance) as client:
            res = await client.get("/api/v3/flaky")
            assert res.json() == {"recovered": True}
            assert route.call_count == 2


@pytest.mark.asyncio
@respx.mock
async def test_base_client_sqlite_lock_detection_and_retry(mock_instance: InstanceConfig):
    """Verify SQLite database lock error detection, backoff retry, and eventual recovery."""
    lock_body = "Microsoft.Data.Sqlite.SqliteException: SQLite Error 5: 'database is locked'."
    route = respx.get("http://radarr.local:7878/api/v3/history").mock(
        side_effect=[
            httpx.Response(500, text=lock_body),
            httpx.Response(200, json={"records": []}),
        ]
    )

    with patch("asyncio.sleep", return_value=None):
        async with BaseArrClient(mock_instance) as client:
            res = await client.get("/api/v3/history")
            assert res.json() == {"records": []}
            assert route.call_count == 2


@pytest.mark.asyncio
@respx.mock
async def test_base_client_sqlite_lock_exhaustion(mock_instance: InstanceConfig):
    """Verify SQLite database lock error raises ArrDatabaseLockedError when retries exhaust."""
    lock_body = "SQLiteBusyException: database is locked"
    respx.get("http://radarr.local:7878/api/v3/history").mock(
        return_value=httpx.Response(500, text=lock_body)
    )

    with patch("asyncio.sleep", return_value=None):
        async with BaseArrClient(mock_instance) as client:
            with pytest.raises(ArrDatabaseLockedError) as exc_info:
                await client.get("/api/v3/history", max_attempts=2)
            assert "database is locked" in str(exc_info.value).lower()


@pytest.mark.asyncio
@respx.mock
async def test_base_client_timeout_handling(mock_instance: InstanceConfig):
    """Verify timeout translates to ArrTimeoutError after retries."""
    respx.get("http://radarr.local:7878/api/v3/slow").mock(
        side_effect=httpx.ReadTimeout("Read timed out")
    )

    with patch("asyncio.sleep", return_value=None):
        async with BaseArrClient(mock_instance) as client:
            with pytest.raises(ArrTimeoutError) as exc_info:
                await client.get("/api/v3/slow", max_attempts=2)
            assert "Timeout" in str(exc_info.value)


@pytest.mark.asyncio
@respx.mock
async def test_base_client_connection_error_handling(mock_instance: InstanceConfig):
    """Verify connection failure translates to ArrConnectionError after retries."""
    respx.get("http://radarr.local:7878/api/v3/unreachable").mock(
        side_effect=httpx.ConnectError("Connection refused")
    )

    with patch("asyncio.sleep", return_value=None):
        async with BaseArrClient(mock_instance) as client:
            with pytest.raises(ArrConnectionError) as exc_info:
                await client.get("/api/v3/unreachable", max_attempts=2)
            assert "Connection failed" in str(exc_info.value)
