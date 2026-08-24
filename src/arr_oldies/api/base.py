"""Base async client for communicating with Radarr and Sonarr REST APIs."""

import asyncio
import random
from typing import Any, Self

import httpx

from arr_oldies.constants import (
    API_KEY_HEADER,
    DEFAULT_BACKOFF_FACTOR,
    DEFAULT_CONNECT_TIMEOUT,
    DEFAULT_KEEPALIVE_CONNECTIONS,
    DEFAULT_KEEPALIVE_EXPIRY,
    DEFAULT_MAX_BACKOFF,
    DEFAULT_MAX_CONNECTIONS,
    DEFAULT_RETRY_ATTEMPTS,
    DEFAULT_TIMEOUT,
    DEFAULT_USER_AGENT,
)
from arr_oldies.exceptions import (
    ArrAuthenticationError,
    ArrClientError,
    ArrConnectionError,
    ArrDatabaseLockedError,
    ArrNotFoundError,
    ArrResponseError,
    ArrTimeoutError,
)
from arr_oldies.models import InstanceConfig


class BaseArrClient:
    """Foundational async HTTP client for *arr API services.

    Handles connection pooling, header injection, exponential backoff with jitter,
    SQLite lock detection, and credential protection.
    """

    def __init__(
        self,
        instance: InstanceConfig,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.instance = instance
        self._client = client
        self._owns_client = client is None

    @property
    def client(self) -> httpx.AsyncClient:
        """Lazily initialize the underlying HTTPX async client."""
        if self._client is None or self._client.is_closed:
            limits = httpx.Limits(
                max_connections=DEFAULT_MAX_CONNECTIONS,
                max_keepalive_connections=DEFAULT_KEEPALIVE_CONNECTIONS,
                keepalive_expiry=DEFAULT_KEEPALIVE_EXPIRY,
            )
            timeout = httpx.Timeout(
                timeout=self.instance.timeout if self.instance.timeout is not None else DEFAULT_TIMEOUT,
                connect=DEFAULT_CONNECT_TIMEOUT,
            )
            headers = {
                API_KEY_HEADER: self.instance.api_key.get_secret_value(),
                "User-Agent": DEFAULT_USER_AGENT,
                "Accept": "application/json",
            }
            verify = self.instance.verify_ssl if self.instance.verify_ssl is not None else True

            self._client = httpx.AsyncClient(
                base_url=self.instance.url,
                headers=headers,
                timeout=timeout,
                limits=limits,
                verify=verify,
            )
            self._owns_client = True
        return self._client

    async def __aenter__(self) -> Self:
        """Async context manager entry."""
        _ = self.client
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Async context manager exit."""
        await self.close()

    async def close(self) -> None:
        """Close the underlying client connection pool if owned."""
        if self._owns_client and self._client is not None and not self._client.is_closed:
            await self._client.aclose()

    def _is_sqlite_lock(self, response: httpx.Response) -> bool:
        """Check whether the response indicates an SQLite database lock error."""
        if response.status_code in (500, 503):
            text = response.text.lower()
            return (
                "database is locked" in text
                or "sqlitebusyexception" in text
                or "sqlite error 5" in text
            )
        return False

    def _calculate_backoff(
        self, attempt: int, response: httpx.Response | None = None
    ) -> float:
        """Calculate exponential backoff delay with random jitter and Retry-After support."""
        if response is not None and response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            if retry_after:
                try:
                    delay = float(retry_after)
                    return min(max(delay, 0.1), DEFAULT_MAX_BACKOFF)
                except ValueError:
                    pass

        delay = DEFAULT_BACKOFF_FACTOR * (2**attempt) + random.uniform(0.0, 0.2)
        return min(delay, DEFAULT_MAX_BACKOFF)

    def _handle_http_error(self, response: httpx.Response) -> None:
        """Translate HTTP error responses into typed domain exceptions."""
        if response.status_code in (401, 403):
            raise ArrAuthenticationError(
                f"Authentication failed ({response.status_code}): check API key for '{self.instance.name}'"
            )
        if response.status_code == 404:
            raise ArrNotFoundError(
                f"Resource not found (404) on '{self.instance.name}': {response.url.path}"
            )
        if self._is_sqlite_lock(response):
            raise ArrDatabaseLockedError(
                f"SQLite database is locked on '{self.instance.name}'"
            )
        raise ArrResponseError(
            status_code=response.status_code,
            message=f"Request to '{self.instance.name}' ({response.url.path}) returned HTTP {response.status_code}: {response.text[:200]}",
        )

    async def request(
        self,
        method: str,
        endpoint: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any = None,
        max_attempts: int = DEFAULT_RETRY_ATTEMPTS,
        **kwargs: Any,
    ) -> httpx.Response:
        """Execute an HTTP request with retry logic for transient and SQLite lock errors."""
        client = self.client
        last_exception: Exception | None = None

        for attempt in range(max_attempts):
            try:
                response = await client.request(
                    method=method,
                    url=endpoint,
                    params=params,
                    json=json,
                    **kwargs,
                )

                # Check if retryable transient error
                is_lock = self._is_sqlite_lock(response)
                is_transient = response.status_code in (429, 502, 503, 504) or is_lock

                if is_transient and attempt < max_attempts - 1:
                    delay = self._calculate_backoff(attempt, response)
                    await asyncio.sleep(delay)
                    continue

                if response.is_error:
                    self._handle_http_error(response)

                return response

            except httpx.TimeoutException as exc:
                last_exception = ArrTimeoutError(
                    f"Timeout connecting to or reading from '{self.instance.name}': {exc}"
                )
                if attempt < max_attempts - 1:
                    delay = self._calculate_backoff(attempt)
                    await asyncio.sleep(delay)
                    continue
                raise last_exception from exc

            except (httpx.ConnectError, httpx.NetworkError, httpx.TransportError) as exc:
                last_exception = ArrConnectionError(
                    f"Connection failed for '{self.instance.name}' ({self.instance.url}): {exc}"
                )
                if attempt < max_attempts - 1:
                    delay = self._calculate_backoff(attempt)
                    await asyncio.sleep(delay)
                    continue
                raise last_exception from exc

            except ArrClientError:
                raise

            except Exception as exc:
                raise ArrClientError(
                    f"Unexpected error communicating with '{self.instance.name}': {exc}"
                ) from exc

        if last_exception is not None:
            raise last_exception
        raise ArrClientError(f"Request to '{self.instance.name}' failed after {max_attempts} attempts")

    async def get(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """Perform an async GET request."""
        return await self.request("GET", endpoint, params=params, **kwargs)

    async def post(
        self,
        endpoint: str,
        json: Any = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """Perform an async POST request."""
        return await self.request("POST", endpoint, json=json, **kwargs)

    async def put(
        self,
        endpoint: str,
        json: Any = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """Perform an async PUT request."""
        return await self.request("PUT", endpoint, json=json, **kwargs)

    async def delete(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """Perform an async DELETE request."""
        return await self.request("DELETE", endpoint, params=params, **kwargs)
