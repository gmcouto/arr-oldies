"""Unit tests for Pydantic v2 schemas, URL sanitization, and SecretStr credential protection."""

import pytest
from pydantic import ValidationError

from arr_oldies.models import (
    AppConfig,
    DefaultsConfig,
    InstanceConfig,
    InstanceType,
    ProbeResult,
)


def test_url_normalization() -> None:
    """Verify trailing slashes and whitespace are stripped from URLs."""
    inst = InstanceConfig(
        name="radarr-test",
        type=InstanceType.RADARR,
        url="  http://localhost:7878///  ",
        api_key="secret_key",  # type: ignore[arg-type]
    )
    assert inst.url == "http://localhost:7878"


def test_invalid_url_scheme() -> None:
    """Verify non-http/https URLs are rejected."""
    with pytest.raises(ValidationError) as exc_info:
        InstanceConfig(
            name="radarr-ftp",
            type=InstanceType.RADARR,
            url="ftp://localhost:7878",
            api_key="secret_key",  # type: ignore[arg-type]
        )
    assert "URL must start with http:// or https://" in str(exc_info.value)

    with pytest.raises(ValidationError) as exc_info2:
        InstanceConfig(
            name="radarr-no-proto",
            type=InstanceType.RADARR,
            url="localhost:7878",
            api_key="secret_key",  # type: ignore[arg-type]
        )
    assert "URL must start with http:// or https://" in str(exc_info2.value)


def test_duplicate_instance_name_rejection() -> None:
    """Verify duplicate instance names (case-insensitive) are rejected."""
    with pytest.raises(ValidationError) as exc_info:
        AppConfig(
            instances=[
                InstanceConfig(
                    name="Radarr-Main",
                    type=InstanceType.RADARR,
                    url="http://localhost:7878",
                    api_key="key1",  # type: ignore[arg-type]
                ),
                InstanceConfig(
                    name="radarr-main",
                    type=InstanceType.RADARR,
                    url="http://localhost:7879",
                    api_key="key2",  # type: ignore[arg-type]
                ),
            ]
        )
    assert "Duplicate instance name found: 'radarr-main'" in str(exc_info.value)


def test_defaults_inheritance() -> None:
    """Verify instances inherit global defaults unless overridden."""
    config = AppConfig(
        defaults=DefaultsConfig(timeout=40.0, verify_ssl=False),
        instances=[
            InstanceConfig(
                name="radarr-default",
                type=InstanceType.RADARR,
                url="http://localhost:7878",
                api_key="key1",  # type: ignore[arg-type]
            ),
            InstanceConfig(
                name="sonarr-override",
                type=InstanceType.SONARR,
                url="https://sonarr.local:8989",
                api_key="key2",  # type: ignore[arg-type]
                timeout=15.0,
                verify_ssl=True,
            ),
        ],
    )
    # radarr-default inherits from defaults
    assert config.instances[0].timeout == 40.0
    assert config.instances[0].verify_ssl is False

    # sonarr-override retains explicit overrides
    assert config.instances[1].timeout == 15.0
    assert config.instances[1].verify_ssl is True


def test_secret_str_masking() -> None:
    """Verify SecretStr masks API keys in string outputs and model_dump representations."""
    raw_key = "super_secret_api_key_99999"
    inst = InstanceConfig(
        name="radarr-secure",
        type=InstanceType.RADARR,
        url="http://localhost:7878",
        api_key=raw_key,  # type: ignore[arg-type]
    )

    # get_secret_value returns the plain text
    assert inst.api_key.get_secret_value() == raw_key

    # str() and repr() do NOT reveal the secret
    assert raw_key not in str(inst)
    assert raw_key not in repr(inst)
    assert raw_key not in repr(inst.api_key)

    # model_dump() masks the SecretStr
    dumped = inst.model_dump()
    assert dumped["api_key"] != raw_key


def test_probe_result_model() -> None:
    """Verify ProbeResult schema construction."""
    res = ProbeResult(
        instance_name="radarr-main",
        instance_type=InstanceType.RADARR,
        url="http://localhost:7878",
        success=True,
        version="5.3.6.8777",
        latency_ms=12.5,
    )
    assert res.success is True
    assert res.version == "5.3.6.8777"
    assert res.latency_ms == 12.5
    assert res.error_message is None
