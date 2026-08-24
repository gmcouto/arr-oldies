"""Async HTTPX health and status prober for Radarr and Sonarr instances."""

import asyncio
import time
from typing import Any
import httpx

from arr_oldies.constants import (
    API_KEY_HEADER,
    API_STATUS_ENDPOINT,
    DEFAULT_CONNECT_TIMEOUT,
    DEFAULT_TIMEOUT,
    DEFAULT_USER_AGENT,
)
from arr_oldies.models import InstanceConfig, ProbeResult


async def probe_single_instance(
    instance: InstanceConfig,
    client: httpx.AsyncClient | None = None,
) -> ProbeResult:
    """Probe a single *arr instance for connectivity, authentication, and version.

    Args:
        instance: The target instance configuration.
        client: Optional existing HTTPX async client. If None, a dedicated client is created.

    Returns:
        ProbeResult object with version, latency, and success/error status.
    """
    target_url = f"{instance.url}{API_STATUS_ENDPOINT}"
    headers = {
        API_KEY_HEADER: instance.api_key.get_secret_value(),
        "User-Agent": DEFAULT_USER_AGENT,
        "Accept": "application/json",
    }
    timeout_val = instance.timeout or DEFAULT_TIMEOUT
    timeout = httpx.Timeout(timeout=timeout_val, connect=DEFAULT_CONNECT_TIMEOUT)
    verify_ssl = instance.verify_ssl if instance.verify_ssl is not None else True

    start_time = time.perf_counter()
    should_close_client = False

    if client is None:
        client = httpx.AsyncClient(verify=verify_ssl)
        should_close_client = True

    try:
        response = await client.get(target_url, headers=headers, timeout=timeout)
        latency_ms = (time.perf_counter() - start_time) * 1000.0

        if response.status_code == 200:
            data: dict[str, Any] = response.json()
            version = str(data.get("version", "Unknown"))
            return ProbeResult(
                instance_name=instance.name,
                instance_type=instance.type,
                url=instance.url,
                success=True,
                version=version,
                latency_ms=latency_ms,
            )
        elif response.status_code in (401, 403):
            return ProbeResult(
                instance_name=instance.name,
                instance_type=instance.type,
                url=instance.url,
                success=False,
                latency_ms=latency_ms,
                error_message=f"{response.status_code} Unauthorized (Invalid API Key)",
            )
        elif response.status_code == 404:
            return ProbeResult(
                instance_name=instance.name,
                instance_type=instance.type,
                url=instance.url,
                success=False,
                latency_ms=latency_ms,
                error_message="404 Not Found (Invalid base URL or endpoint)",
            )
        else:
            return ProbeResult(
                instance_name=instance.name,
                instance_type=instance.type,
                url=instance.url,
                success=False,
                latency_ms=latency_ms,
                error_message=f"HTTP {response.status_code}: {response.reason_phrase}",
            )
    except httpx.ConnectError:
        latency_ms = (time.perf_counter() - start_time) * 1000.0
        return ProbeResult(
            instance_name=instance.name,
            instance_type=instance.type,
            url=instance.url,
            success=False,
            latency_ms=latency_ms,
            error_message="Connection refused / Host unreachable",
        )
    except httpx.TimeoutException:
        latency_ms = (time.perf_counter() - start_time) * 1000.0
        return ProbeResult(
            instance_name=instance.name,
            instance_type=instance.type,
            url=instance.url,
            success=False,
            latency_ms=latency_ms,
            error_message=f"Connection timed out (> {timeout_val}s)",
        )
    except Exception as exc:
        latency_ms = (time.perf_counter() - start_time) * 1000.0
        return ProbeResult(
            instance_name=instance.name,
            instance_type=instance.type,
            url=instance.url,
            success=False,
            latency_ms=latency_ms,
            error_message=f"Network error: {type(exc).__name__}",
        )
    finally:
        if should_close_client and client is not None:
            await client.aclose()


async def probe_all_instances(instances: list[InstanceConfig]) -> list[ProbeResult]:
    """Concurrently probe all specified instances.

    Args:
        instances: List of InstanceConfig instances to probe.

    Returns:
        List of ProbeResult objects in the order of input instances.
    """
    if not instances:
        return []

    tasks = [probe_single_instance(inst) for inst in instances]
    results: list[ProbeResult] = await asyncio.gather(*tasks)
    return results
