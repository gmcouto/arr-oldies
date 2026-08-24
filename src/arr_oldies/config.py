"""Hierarchical configuration loader, file discovery, and schema validation."""

from pathlib import Path
from typing import Any

import pydantic
import yaml

from arr_oldies.constants import CONFIG_FILENAMES
from arr_oldies.exceptions import (
    ConfigFormatError,
    ConfigNotFoundError,
    ConfigValidationError,
)
from arr_oldies.models import AppConfig


def find_config_file(explicit_path: Path | str | None = None) -> Path:
    """Discover configuration file path based on explicit flag, CWD, or user home directory.

    Precedence:
    1. Explicit path passed by caller (e.g. CLI --config flag)
    2. Current working directory (./arr-oldies.yaml, ./arr-oldies.yml, ./config.yaml, ./config.yml)
    3. User home config (~/.config/arr-oldies/config.yaml, .yml, arr-oldies.yaml, .yml)
    """
    if explicit_path is not None:
        path = Path(explicit_path).expanduser().resolve()
        if not path.is_file():
            raise ConfigNotFoundError(f"Specified config file not found: {explicit_path}")
        return path

    searched_locations: list[Path] = []

    # 1. Search current working directory
    cwd = Path.cwd()
    for filename in CONFIG_FILENAMES:
        candidate = cwd / filename
        searched_locations.append(candidate)
        if candidate.is_file():
            return candidate.resolve()

    # 2. Search ~/.config/arr-oldies/
    user_config_dir = Path.home() / ".config" / "arr-oldies"
    # Order per D-01: config.yaml, config.yml, arr-oldies.yaml, arr-oldies.yml
    home_filenames = ["config.yaml", "config.yml", "arr-oldies.yaml", "arr-oldies.yml"]
    for filename in home_filenames:
        candidate = user_config_dir / filename
        searched_locations.append(candidate)
        if candidate.is_file():
            return candidate.resolve()

    locations_str = "\n  - " + "\n  - ".join(str(loc) for loc in searched_locations)
    raise ConfigNotFoundError(
        f"No configuration file found. Searched the following locations:{locations_str}"
    )


def _format_validation_error(exc: pydantic.ValidationError, path: Path) -> str:
    """Format Pydantic ValidationError into a clean, human-readable diagnostic message."""
    errors = exc.errors()
    lines = [f"Configuration validation failed for {path}:"]
    for err in errors:
        loc = " -> ".join(str(item) for item in err["loc"]) if err["loc"] else "root"
        msg = err["msg"]
        lines.append(f"  - [{loc}]: {msg}")
    return "\n".join(lines)


def load_config(config_path: Path | str | None = None) -> AppConfig:
    """Load, parse, and validate application configuration from YAML.

    Raises:
        ConfigNotFoundError: If the configuration file cannot be found.
        ConfigFormatError: If the YAML syntax is invalid.
        ConfigValidationError: If schema validation fails.
    """
    resolved_path = find_config_file(config_path)

    try:
        content = resolved_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigNotFoundError(f"Failed to read config file {resolved_path}: {exc}") from exc

    try:
        data: Any = yaml.safe_load(content)
    except yaml.YAMLError as exc:
        raise ConfigFormatError(f"Invalid YAML syntax in {resolved_path}: {exc}") from exc

    if data is None:
        raise ConfigValidationError(f"Configuration file is empty: {resolved_path}")

    if not isinstance(data, dict):
        raise ConfigValidationError(
            f"Root configuration must be a mapping (key-value dictionary) in {resolved_path}"
        )

    try:
        return AppConfig.model_validate(data)
    except pydantic.ValidationError as exc:
        formatted_msg = _format_validation_error(exc, resolved_path)
        raise ConfigValidationError(formatted_msg) from exc
