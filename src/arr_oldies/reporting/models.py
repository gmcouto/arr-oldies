"""Data models and enums for reporting and visualization."""

from enum import StrEnum


class OutputFormat(StrEnum):
    """Supported CLI output presentation formats."""

    TABLE = "table"
    JSON = "json"
