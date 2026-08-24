"""Pytest shared fixtures and test utilities."""

from pathlib import Path

import pytest


@pytest.fixture
def sample_valid_yaml() -> str:
    """Return a standard valid multi-instance YAML configuration."""
    return """
defaults:
  timeout: 45.0
  verify_ssl: true

instances:
  - name: radarr-main
    type: radarr
    url: http://localhost:7878/
    api_key: radarr_secret_key_12345
    timeout: 60.0

  - name: sonarr-tv
    type: sonarr
    url: https://sonarr.local:8989
    api_key: sonarr_secret_key_67890
    verify_ssl: false

  - name: radarr-4k
    type: radarr
    url: http://192.168.1.100:7878
    api_key: radarr_4k_key_abcdef
"""


@pytest.fixture
def sample_invalid_syntax_yaml() -> str:
    """Return a YAML string with invalid syntax."""
    return """
defaults:
  timeout: 45.0
instances:
  - name: [unclosed list
"""


@pytest.fixture
def sample_schema_invalid_yaml() -> str:
    """Return a YAML string with missing required fields."""
    return """
instances:
  - name: radarr-missing-url
    type: radarr
    api_key: some_key
"""


@pytest.fixture
def sample_duplicate_instances_yaml() -> str:
    """Return a YAML string with duplicate instance names (case-insensitive)."""
    return """
instances:
  - name: Radarr-Main
    type: radarr
    url: http://localhost:7878
    api_key: key1

  - name: radarr-main
    type: radarr
    url: http://localhost:7879
    api_key: key2
"""


@pytest.fixture
def config_file_path(tmp_path: Path, sample_valid_yaml: str) -> Path:
    """Create a temporary valid config.yaml file and return its path."""
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text(sample_valid_yaml, encoding="utf-8")
    return cfg_file
