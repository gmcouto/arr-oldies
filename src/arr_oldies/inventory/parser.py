"""Human-friendly string parsing for file sizes, age intervals, and date cutoffs."""

import re
from datetime import UTC, datetime

from arr_oldies.exceptions import ParseError

SIZE_REGEX = re.compile(r"^\s*([0-9]+(?:\.[0-9]+)?)\s*([a-zA-Z]*)\s*$")
AGE_REGEX = re.compile(r"^\s*([0-9]+)\s*([a-zA-Z]*)\s*$")

SIZE_MULTIPLIERS: dict[str, int] = {
    "": 1,
    "b": 1,
    "k": 1024,
    "kb": 1000,
    "kib": 1024,
    "m": 1024**2,
    "mb": 1000**2,
    "mib": 1024**2,
    "g": 1024**3,
    "gb": 1000**3,
    "gib": 1024**3,
    "t": 1024**4,
    "tb": 1000**4,
    "tib": 1024**4,
}


def parse_size(size_str: str) -> int:
    """Parse human size string (e.g., '500MB', '2GB', '1.5GiB', '100M') into integer bytes."""
    match = SIZE_REGEX.match(size_str)
    if not match:
        raise ParseError(f"Invalid size specification: '{size_str}'. Examples: '500MB', '2GB', '1.5GiB'.")

    val_str, unit_raw = match.groups()
    unit = unit_raw.lower()

    multiplier = SIZE_MULTIPLIERS.get(unit)
    if multiplier is None:
        raise ParseError(
            f"Unknown size unit '{unit_raw}' in '{size_str}'. Supported: B, KB, KiB, MB, MiB, GB, GiB, TB, TiB."
        )

    return int(float(val_str) * multiplier)


def parse_age_cutoff(age_str: str) -> int:
    """Parse human age interval (e.g., '30d', '6m', '1y', '2w', '90') into integer days."""
    match = AGE_REGEX.match(age_str)
    if not match:
        raise ParseError(f"Invalid age specification: '{age_str}'. Examples: '30d', '6m', '1y', '2w'.")

    val_str, unit_raw = match.groups()
    val = int(val_str)
    unit = unit_raw.lower()

    if unit in ("", "d", "day", "days"):
        return val
    elif unit in ("w", "week", "weeks"):
        return val * 7
    elif unit in ("m", "month", "months", "mo"):
        return val * 30
    elif unit in ("y", "year", "years", "yr"):
        return val * 365
    else:
        raise ParseError(
            f"Unknown age unit '{unit_raw}' in '{age_str}'. Supported units: d (days), w (weeks), m (months), y (years)."
        )


def parse_date_cutoff(date_str: str) -> datetime:
    """Parse ISO-8601 or YYYY-MM-DD date string into UTC datetime."""
    clean = date_str.strip()
    try:
        if "T" in clean:
            dt = datetime.fromisoformat(clean)
        else:
            dt = datetime.strptime(clean, "%Y-%m-%d").replace(tzinfo=UTC)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt.astimezone(UTC)
    except (ValueError, TypeError) as exc:
        raise ParseError(f"Invalid date format: '{date_str}'. Expected 'YYYY-MM-DD' or ISO-8601 format.") from exc

