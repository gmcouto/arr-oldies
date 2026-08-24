"""Unit tests for instance targeting, filtering flags, and conflict detection."""

import pytest

from arr_oldies.exceptions import InstanceConflictError, InstanceNotFoundError
from arr_oldies.models import AppConfig, InstanceConfig, InstanceType
from arr_oldies.targeting import resolve_target_instances


@pytest.fixture
def multi_instance_config() -> AppConfig:
    """Create a sample configuration with multiple Radarr and Sonarr instances."""
    return AppConfig(
        instances=[
            InstanceConfig(
                name="radarr-hd",
                type=InstanceType.RADARR,
                url="http://localhost:7878",
                api_key="key1",  # type: ignore[arg-type]
            ),
            InstanceConfig(
                name="radarr-4k",
                type=InstanceType.RADARR,
                url="http://localhost:7879",
                api_key="key2",  # type: ignore[arg-type]
            ),
            InstanceConfig(
                name="sonarr-tv",
                type=InstanceType.SONARR,
                url="http://localhost:8989",
                api_key="key3",  # type: ignore[arg-type]
            ),
            InstanceConfig(
                name="sonarr-anime",
                type=InstanceType.SONARR,
                url="http://localhost:8990",
                api_key="key4",  # type: ignore[arg-type]
            ),
        ]
    )


def test_default_targets_all_instances(multi_instance_config: AppConfig) -> None:
    """Verify default behavior targets all configured instances (D-09)."""
    targets = resolve_target_instances(multi_instance_config)
    assert len(targets) == 4
    names = [inst.name for inst in targets]
    assert names == ["radarr-hd", "radarr-4k", "sonarr-tv", "sonarr-anime"]


def test_filter_radarr_only(multi_instance_config: AppConfig) -> None:
    """Verify --radarr flag filters to only Radarr instances."""
    targets = resolve_target_instances(multi_instance_config, radarr=True)
    assert len(targets) == 2
    assert all(inst.type == InstanceType.RADARR for inst in targets)
    assert [inst.name for inst in targets] == ["radarr-hd", "radarr-4k"]


def test_filter_sonarr_only(multi_instance_config: AppConfig) -> None:
    """Verify --sonarr flag filters to only Sonarr instances."""
    targets = resolve_target_instances(multi_instance_config, sonarr=True)
    assert len(targets) == 2
    assert all(inst.type == InstanceType.SONARR for inst in targets)
    assert [inst.name for inst in targets] == ["sonarr-tv", "sonarr-anime"]


def test_filter_both_flags_targets_all(multi_instance_config: AppConfig) -> None:
    """Verify specifying both --radarr and --sonarr retains all instances."""
    targets = resolve_target_instances(multi_instance_config, radarr=True, sonarr=True)
    assert len(targets) == 4


def test_select_specific_instances_by_name(multi_instance_config: AppConfig) -> None:
    """Verify explicit instance names selection (repeatable -i / --instance)."""
    targets = resolve_target_instances(
        multi_instance_config, instance_names=["Radarr-4k", "sonarr-tv"]
    )
    assert len(targets) == 2
    assert targets[0].name == "radarr-4k"
    assert targets[1].name == "sonarr-tv"


def test_unknown_instance_raises_not_found(multi_instance_config: AppConfig) -> None:
    """Verify selecting an unknown instance name raises InstanceNotFoundError with available names."""
    with pytest.raises(InstanceNotFoundError) as exc_info:
        resolve_target_instances(
            multi_instance_config, instance_names=["non-existent-instance"]
        )
    assert "Instance 'non-existent-instance' not found in configuration" in str(exc_info.value)
    assert "radarr-hd" in str(exc_info.value)


def test_conflicting_radarr_flag_with_sonarr_instance(
    multi_instance_config: AppConfig,
) -> None:
    """Verify selecting Sonarr instance alongside --radarr raises InstanceConflictError (D-10)."""
    with pytest.raises(InstanceConflictError) as exc_info:
        resolve_target_instances(
            multi_instance_config, radarr=True, instance_names=["sonarr-tv"]
        )
    assert "Conflicting target flags" in str(exc_info.value)
    assert "Instance 'sonarr-tv' is Sonarr, but --radarr flag was specified" in str(exc_info.value)


def test_conflicting_sonarr_flag_with_radarr_instance(
    multi_instance_config: AppConfig,
) -> None:
    """Verify selecting Radarr instance alongside --sonarr raises InstanceConflictError (D-10)."""
    with pytest.raises(InstanceConflictError) as exc_info:
        resolve_target_instances(
            multi_instance_config, sonarr=True, instance_names=["radarr-hd"]
        )
    assert "Conflicting target flags" in str(exc_info.value)
    assert "Instance 'radarr-hd' is Radarr, but --sonarr flag was specified" in str(exc_info.value)


def test_filter_no_matches_raises_not_found() -> None:
    """Verify filtering that produces zero instances raises InstanceNotFoundError."""
    config = AppConfig(
        instances=[
            InstanceConfig(
                name="sonarr-only",
                type=InstanceType.SONARR,
                url="http://localhost:8989",
                api_key="key",  # type: ignore[arg-type]
            )
        ]
    )
    with pytest.raises(InstanceNotFoundError) as exc_info:
        resolve_target_instances(config, radarr=True)
    assert "No matching instances found" in str(exc_info.value)
