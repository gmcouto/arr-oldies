"""Integration tests for Typer CLI commands, options, banner, and exit codes."""

from pathlib import Path

import respx
from typer.testing import CliRunner

from arr_oldies import __version__
from arr_oldies.cli import app

runner = CliRunner()


def test_bare_cli_invocation_shows_banner() -> None:
    """Verify invoking arr-oldies with no arguments displays welcome banner and exits 0."""
    result = runner.invoke(app, [])
    assert result.exit_code == 0
    assert "Welcome to Arr-Oldies" in result.output
    assert "validate-config" in result.output


def test_version_flag() -> None:
    """Verify --version flag prints version string and exits 0."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert f"arr-oldies {__version__}" in result.output


@respx.mock
def test_validate_config_all_healthy(tmp_path: Path, sample_valid_yaml: str) -> None:
    """Verify validate-config with all healthy instances exits 0 and prints table."""
    cfg = tmp_path / "config.yaml"
    cfg.write_text(sample_valid_yaml, encoding="utf-8")

    respx.get("http://localhost:7878/api/v3/system/status").respond(
        status_code=200, json={"version": "5.3.6"}
    )
    respx.get("https://sonarr.local:8989/api/v3/system/status").respond(
        status_code=200, json={"version": "4.0.1"}
    )
    respx.get("http://192.168.1.100:7878/api/v3/system/status").respond(
        status_code=200, json={"version": "5.3.6"}
    )

    result = runner.invoke(app, ["--config", str(cfg), "validate-config"])
    assert result.exit_code == 0
    assert "Instance Validation Results" in result.output
    assert "radarr-main" in result.output
    assert "sonarr-tv" in result.output
    assert "radarr-4k" in result.output
    assert "[OK]" in result.output


@respx.mock
def test_validate_config_subcommand_config_flag(
    tmp_path: Path, sample_valid_yaml: str
) -> None:
    """Verify validate-config works when --config is passed after the subcommand."""
    cfg = tmp_path / "config.yaml"
    cfg.write_text(sample_valid_yaml, encoding="utf-8")

    respx.get("http://localhost:7878/api/v3/system/status").respond(
        status_code=200, json={"version": "5.3.6"}
    )

    result = runner.invoke(app, ["validate-config", "--config", str(cfg), "-i", "radarr-main"])
    assert result.exit_code == 0
    assert "radarr-main" in result.output


@respx.mock
def test_validate_config_partial_failure_exits_1(
    tmp_path: Path, sample_valid_yaml: str
) -> None:
    """Verify validate-config with a failing instance exits with code 1."""
    cfg = tmp_path / "config.yaml"
    cfg.write_text(sample_valid_yaml, encoding="utf-8")

    respx.get("http://localhost:7878/api/v3/system/status").respond(
        status_code=200, json={"version": "5.3.6"}
    )
    respx.get("https://sonarr.local:8989/api/v3/system/status").respond(
        status_code=401
    )
    respx.get("http://192.168.1.100:7878/api/v3/system/status").respond(
        status_code=200, json={"version": "5.3.6"}
    )

    result = runner.invoke(app, ["--config", str(cfg), "validate-config"])
    assert result.exit_code == 1
    assert "Instance Validation Results" in result.output
    assert "[FAIL]" in result.output


def test_validate_config_missing_file_exits_2(tmp_path: Path) -> None:
    """Verify non-existent config file writes error to stderr and exits with code 2."""
    missing = tmp_path / "missing.yaml"
    result = runner.invoke(app, ["--config", str(missing), "validate-config"])
    assert result.exit_code == 2
    assert "Error:" in result.output
    assert "Specified config file not found" in result.output


def test_validate_config_invalid_yaml_exits_2(
    tmp_path: Path, sample_invalid_syntax_yaml: str
) -> None:
    """Verify invalid YAML syntax writes error to stderr and exits with code 2."""
    bad_cfg = tmp_path / "bad.yaml"
    bad_cfg.write_text(sample_invalid_syntax_yaml, encoding="utf-8")

    result = runner.invoke(app, ["--config", str(bad_cfg), "validate-config"])
    assert result.exit_code == 2
    assert "Error:" in result.output
    assert "Invalid YAML syntax" in result.output


def test_validate_config_unknown_instance_exits_2(
    tmp_path: Path, sample_valid_yaml: str
) -> None:
    """Verify selecting unknown instance name writes error to stderr and exits with code 2."""
    cfg = tmp_path / "config.yaml"
    cfg.write_text(sample_valid_yaml, encoding="utf-8")

    result = runner.invoke(
        app, ["--config", str(cfg), "validate-config", "-i", "nonexistent"]
    )
    assert result.exit_code == 2
    assert "Error:" in result.output
    assert "Instance 'nonexistent' not found in configuration" in result.output


def test_validate_config_conflicting_flags_exits_2(
    tmp_path: Path, sample_valid_yaml: str
) -> None:
    """Verify conflicting targeting flags (--radarr + sonarr instance) writes error to stderr and exits with code 2."""
    cfg = tmp_path / "config.yaml"
    cfg.write_text(sample_valid_yaml, encoding="utf-8")

    result = runner.invoke(
        app, ["--config", str(cfg), "validate-config", "--radarr", "-i", "sonarr-tv"]
    )
    assert result.exit_code == 2
    assert "Error:" in result.output
    assert "Conflicting target flags" in result.output
