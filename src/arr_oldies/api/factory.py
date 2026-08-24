"""Factory for creating typed Radarr or Sonarr API clients."""

import httpx

from arr_oldies.api.radarr import RadarrClient
from arr_oldies.api.sonarr import SonarrClient
from arr_oldies.models import InstanceConfig, InstanceType


def create_client(
    instance: InstanceConfig,
    client: httpx.AsyncClient | None = None,
) -> RadarrClient | SonarrClient:
    """Instantiate a typed API client based on InstanceConfig.type."""
    if instance.type == InstanceType.RADARR:
        return RadarrClient(instance, client=client)
    elif instance.type == InstanceType.SONARR:
        return SonarrClient(instance, client=client)
    raise ValueError(f"Unsupported instance type: '{instance.type}'")
