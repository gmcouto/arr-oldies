"""Instance targeting, filtering, and conflict resolution logic."""

from arr_oldies.exceptions import InstanceConflictError, InstanceNotFoundError
from arr_oldies.models import AppConfig, InstanceConfig, InstanceType


def resolve_target_instances(
    config: AppConfig,
    radarr: bool = False,
    sonarr: bool = False,
    instance_names: list[str] | None = None,
) -> list[InstanceConfig]:
    """Resolve the list of target instances according to explicit names and service type filters.

    Args:
        config: Loaded AppConfig object.
        radarr: If True, filter candidate instances to Radarr instances only.
        sonarr: If True, filter candidate instances to Sonarr instances only.
        instance_names: Optional list of explicit instance names to select.

    Returns:
        List of matched InstanceConfig objects.

    Raises:
        InstanceNotFoundError: If an explicit instance name does not exist, or no matching
                               instances are found.
        InstanceConflictError: If conflicting flags are specified (e.g., --radarr with a Sonarr instance).
    """
    instances_by_name: dict[str, InstanceConfig] = {
        inst.name.lower(): inst for inst in config.instances
    }

    # Step 1: Explicit Instance Selection
    selected_instances: list[InstanceConfig] = []
    has_explicit_names = bool(instance_names)

    if has_explicit_names and instance_names is not None:
        for raw_name in instance_names:
            norm_name = raw_name.strip().lower()
            if norm_name not in instances_by_name:
                available = ", ".join(inst.name for inst in config.instances) or "None"
                raise InstanceNotFoundError(
                    f"Instance '{raw_name}' not found in configuration. Available instances: {available}"
                )
            selected_instances.append(instances_by_name[norm_name])
    else:
        selected_instances = list(config.instances)

    # Step 2: Service Flag Filtering & Conflict Enforcement
    if radarr and not sonarr:
        if has_explicit_names:
            for inst in selected_instances:
                if inst.type != InstanceType.RADARR:
                    raise InstanceConflictError(
                        f"Conflicting target flags: Instance '{inst.name}' is Sonarr, but --radarr flag was specified."
                    )
        selected_instances = [
            inst for inst in selected_instances if inst.type == InstanceType.RADARR
        ]
    elif sonarr and not radarr:
        if has_explicit_names:
            for inst in selected_instances:
                if inst.type != InstanceType.SONARR:
                    raise InstanceConflictError(
                        f"Conflicting target flags: Instance '{inst.name}' is Radarr, but --sonarr flag was specified."
                    )
        selected_instances = [
            inst for inst in selected_instances if inst.type == InstanceType.SONARR
        ]

    # Step 3: Check empty results
    if not selected_instances:
        raise InstanceNotFoundError("No matching instances found for the specified target filters.")

    return selected_instances
