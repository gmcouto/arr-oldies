"""Unit tests for configuration file discovery, YAML parsing, and schema validation diagnostics."""

import os
from pathlib import Path
import pytest

from arr_oldies.config import find_config_file, load_config
from arr_oldies.exceptions import (
    ConfigFormatError,
    ConfigNotFoundError,
    ConfigValidationError,
)
from arr_oldies.models import InstanceType


def test_explicit_config_found(tmp_path: Path, sample_valid_yaml: str) -> None:
    """Verify explicit config file path is resolved correctly."""
    cfg = tmp_path / "my-custom-config.yaml"
    cfg.write_text(sample_valid_yaml, encoding="utf-8")

    found = find_config_file(cfg)
    assert found == cfg.resolve()

    app_config = load_config(cfg)
    assert len(app_config.instances) == 3
    assert app_config.instances[0].name == "radarr-main"
    assert app_config.instances[0].type == InstanceType.RADARR
    assert app_config.instances[1].name == "sonarr-tv"
    assert app_config.instances[1].type == InstanceType.SONARR


def test_explicit_config_not_found(tmp_path: Path) -> None:
    """Verify non-existent explicit config path raises ConfigNotFoundError."""
    missing = tmp_path / "non_existent.yaml"
    with pytest.raises(ConfigNotFoundError) as exc_info:
        find_config_file(missing)
    assert "Specified config file not found" in str(exc_info.value)


def test_discovery_cwd_precedence(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify CWD discovery order (arr-oldies.yaml takes precedence over config.yaml)."""
    monkeypatch.chdir(tmp_path)

    cfg1 = tmp_path / "config.yaml"
    cfg1.write_text("instances: []", encoding="utf-8")

    cfg2 = tmp_path / "arr-oldies.yaml"
    cfg2.write_text("instances: []", encoding="utf-8")

    found = find_config_file()
    assert found == cfg2.resolve()


def test_discovery_home_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify fallback to ~/.config/arr-oldies/ when CWD has no config file."""
    cwd_dir = tmp_path / "cwd"
    cwd_dir.mkdir()
    monkeypatch.chdir(cwd_dir)

    home_dir = tmp_path / "home"
    home_config_dir = home_dir / ".config" / "arr-oldies"
    home_config_dir.mkdir(parents=True)
    home_cfg = home_config_dir / "config.yaml"
    home_cfg.write_text("instances: []", encoding="utf-8")

    monkeypatch.setattr(Path, "home", lambda: home_dir)

    found = find_config_file()
    assert found == home_cfg.resolve()


def test_discovery_not_found_anywhere(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify ConfigNotFoundError lists searched locations when no file exists."""
    empty_cwd = tmp_path / "empty_cwd"
    empty_cwd.mkdir()
    monkeypatch.chdir(empty_cwd)

    empty_home = tmp_path / "empty_home"
    empty_home.mkdir()
    monkeypatch.setattr(Path, "home", lambda: empty_home)

    with pytest.raises(ConfigNotFoundError) as exc_info:
        find_config_file()
    assert "No configuration file found" in str(exc_info.value)
    assert "arr-oldies.yaml" in str(exc_info.value)


def test_load_malformed_yaml_syntax(tmp_path: Path, sample_invalid_syntax_yaml: str) -> None:
    """Verify invalid YAML syntax raises ConfigFormatError."""
    bad_cfg = tmp_path / "bad.yaml"
    bad_cfg.write_text(sample_invalid_syntax_yaml, encoding="utf-8")

    with pytest.raises(ConfigFormatError) as exc_info:
        load_config(bad_cfg)
    assert "Invalid YAML syntax" in str(exc_info.value)


def test_load_empty_config(tmp_path: Path) -> None:
    """Verify empty configuration file raises ConfigValidationError."""
    empty_cfg = tmp_path / "empty.yaml"
    empty_cfg.write_text("", encoding="utf-8")

    with pytest.raises(ConfigValidationError) as exc_info:
        load_config(empty_cfg)
    assert "Configuration file is empty" in str(exc_info.value)


def test_load_non_mapping_yaml(tmp_path: Path) -> None:
    """Verify YAML that is a list or scalar instead of a dict raises ConfigValidationError."""
    list_cfg = tmp_path / "list.yaml"
    list_cfg.write_text("- item1\n- item2\n", encoding="utf-8")

    with pytest.raises(ConfigValidationError) as exc_info:
        load_config(list_cfg)
    assert "Root configuration must be a mapping" in str(exc_info.value)


def test_load_schema_validation_error(
    tmp_path: Path, sample_schema_invalid_yaml: str
) -> None:
    """Verify schema violations raise ConfigValidationError with diagnostic detail."""
    invalid_cfg = tmp_path / "invalid_schema.yaml"
    invalid_cfg.write_text(sample_schema_invalid_yaml, encoding="utf-8")

    with pytest.raises(ConfigValidationError) as exc_info:
        load_config(invalid_cfg)
    assert "Configuration validation failed" in str(exc_info.value)
    assert "url" in str(exc_info.value)
