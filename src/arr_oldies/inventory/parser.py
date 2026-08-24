"""Human-friendly string parsing for file sizes, age intervals, and date cutoffs."""

import re
from datetime import UTC, datetime

from arr_oldies.exceptions import ParseError

SIZE_REGEX = re.compile(r"^\s*([0-9]+(?:\.[0-9]+)?)\s*([a-zA-Z]*)\s*$")
AGE_BARE_INT_REGEX = re.compile(r"^\s*([0-9]+)\s*$")
AGE_TOKEN_REGEX = re.compile(r"([0-9]+)\s*([a-zA-Z]+)")
AGE_DELIMITER_REGEX = re.compile(r"^(?:[\s,]|\band\b|&)*$", re.IGNORECASE)

AGE_UNIT_MULTIPLIERS: dict[str, int] = {
    # Days
    "d": 1,
    "day": 1,
    "days": 1,
    # Weeks
    "w": 7,
    "wk": 7,
    "wks": 7,
    "week": 7,
    "weeks": 7,
    # Months
    "m": 30,
    "mo": 30,
    "mos": 30,
    "month": 30,
    "months": 30,
    # Years
    "y": 365,
    "yr": 365,
    "yrs": 365,
    "year": 365,
    "years": 365,
}

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
        raise ParseError(
            f"Invalid size specification: '{size_str}'. Examples: '500MB', '2GB', '1.5GiB'."
        )

    val_str, unit_raw = match.groups()
    unit = unit_raw.lower()

    multiplier = SIZE_MULTIPLIERS.get(unit)
    if multiplier is None:
        raise ParseError(
            f"Unknown size unit '{unit_raw}' in '{size_str}'. Supported: B, KB, KiB, MB, MiB, GB, GiB, TB, TiB."
        )

    return int(float(val_str) * multiplier)


def parse_age_cutoff(age_str: str) -> int:
    """Parse human age interval (e.g., '30d', '6m', '1y', '2w', '1y1m1d', '2y6m', '90') into integer days."""
    clean = age_str.strip()
    if not clean:
        raise ParseError(
            f"Invalid age specification: '{age_str}'. Examples: '30d', '6m', '1y1m1d', '2w'."
        )

    # Fast path for bare integer inputs (defaulting to days)
    match_bare = AGE_BARE_INT_REGEX.match(clean)
    if match_bare:
        return int(match_bare.group(1))

    # Tokenize composite duration string
    matches = list(AGE_TOKEN_REGEX.finditer(clean))
    if not matches:
        raise ParseError(
            f"Invalid age specification: '{age_str}'. Examples: '30d', '6m', '1y1m1d', '2w'."
        )

    total_days = 0
    current_idx = 0

    for match in matches:
        prefix = clean[current_idx : match.start()]
        if not AGE_DELIMITER_REGEX.match(prefix):
            raise ParseError(
                f"Invalid age specification: '{age_str}'. Examples: '30d', '6m', '1y1m1d', '2w'."
            )

        val_str, unit_raw = match.groups()
        unit = unit_raw.lower()

        multiplier = AGE_UNIT_MULTIPLIERS.get(unit)
        if multiplier is None:
            raise ParseError(
                f"Unknown age unit '{unit_raw}' in '{age_str}'. Supported units: d (days), w (weeks), m (months), y (years)."
            )

        total_days += int(val_str) * multiplier
        current_idx = match.end()

    suffix = clean[current_idx:]
    if not AGE_DELIMITER_REGEX.match(suffix):
        raise ParseError(
            f"Invalid age specification: '{age_str}'. Examples: '30d', '6m', '1y1m1d', '2w'."
        )

    return total_days


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
        raise ParseError(
            f"Invalid date format: '{date_str}'. Expected 'YYYY-MM-DD' or ISO-8601 format."
        ) from exc
