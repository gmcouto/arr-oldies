"""Unit tests for human size, age interval, and date cutoff parsing utilities."""

from datetime import UTC, datetime

import pytest

from arr_oldies.exceptions import ParseError
from arr_oldies.inventory.parser import parse_age_cutoff, parse_date_cutoff, parse_size


@pytest.mark.parametrize(
    "input_str,expected_bytes",
    [
        ("500B", 500),
        ("500b", 500),
        ("500MB", 500 * 1000 * 1000),
        ("500MiB", 500 * 1024 * 1024),
        ("2GB", 2 * 1000 * 1000 * 1000),
        ("2GiB", 2 * 1024 * 1024 * 1024),
        ("1.5GB", int(1.5 * 1000 * 1000 * 1000)),
        ("1TB", 1000**4),
        ("1TiB", 1024**4),
        ("100M", 100 * 1024 * 1024),
        ("1024", 1024),
    ],
)
def test_parse_size_valid(input_str: str, expected_bytes: int):
    """Verify valid human size strings parse to exact byte integers."""
    assert parse_size(input_str) == expected_bytes


def test_parse_size_invalid():
    """Verify invalid size strings raise ParseError with helpful messages."""
    with pytest.raises(ParseError) as exc_info:
        parse_size("invalid_size")
    assert "Invalid size specification" in str(exc_info.value)

    with pytest.raises(ParseError) as exc_info:
        parse_size("500PB")  # Unsupported unit
    assert "Unknown size unit" in str(exc_info.value)


@pytest.mark.parametrize(
    "input_str,expected_days",
    [
        ("30", 30),
        ("30d", 30),
        ("30day", 30),
        ("30days", 30),
        ("2w", 14),
        ("2week", 14),
        ("2weeks", 14),
        ("6m", 180),
        ("6mo", 180),
        ("6month", 180),
        ("6months", 180),
        ("1y", 365),
        ("1yr", 365),
        ("1year", 365),
        ("2years", 730),
        # Composite duration test cases
        ("1y1m1d", 365 + 30 + 1),  # 396
        ("2y6m", 2 * 365 + 6 * 30),  # 910
        ("3w4d", 3 * 7 + 4 * 1),  # 25
        ("1y 2mo 3d", 365 + 2 * 30 + 3),  # 428
        ("1 year 1 month 1 day", 396),
        ("2 weeks, 3 days", 17),
        ("1 year and 2 months", 365 + 60),  # 425
        ("1y & 3w", 365 + 21),  # 386
        ("1Y1M1D", 396),
        ("2Years 6Months", 910),
        ("1d 1m 1y", 396),  # Out-of-order units
        ("1y 1y", 730),  # Repeated units
    ],
)
def test_parse_age_cutoff_valid(input_str: str, expected_days: int):
    """Verify valid age strings parse to integer days."""
    assert parse_age_cutoff(input_str) == expected_days


@pytest.mark.parametrize(
    "invalid_input,expected_error",
    [
        ("bad_age", "Invalid age specification"),
        ("", "Invalid age specification"),
        ("   ", "Invalid age specification"),
        ("30x", "Unknown age unit"),
        ("1y2x3d", "Unknown age unit"),
        ("1y1m1d_extra", "Invalid age specification"),
        ("1y 1m extra", "Invalid age specification"),
        ("-5d", "Invalid age specification"),
        ("1y-2m", "Invalid age specification"),
    ],
)
def test_parse_age_cutoff_invalid(invalid_input: str, expected_error: str):
    """Verify invalid age strings raise ParseError with expected messages."""
    with pytest.raises(ParseError) as exc_info:
        parse_age_cutoff(invalid_input)
    assert expected_error in str(exc_info.value)


def test_parse_date_cutoff_valid():
    """Verify ISO and YYYY-MM-DD date strings parse to UTC timezone-aware datetimes."""
    dt = parse_date_cutoff("2024-01-15")
    assert dt == datetime(2024, 1, 15, 0, 0, 0, tzinfo=UTC)

    dt_iso = parse_date_cutoff("2024-01-15T14:30:00Z")
    assert dt_iso == datetime(2024, 1, 15, 14, 30, 0, tzinfo=UTC)

    dt_offset = parse_date_cutoff("2024-01-15T16:30:00+02:00")
    assert dt_offset == datetime(2024, 1, 15, 14, 30, 0, tzinfo=UTC)


def test_parse_date_cutoff_invalid():
    """Verify invalid date strings raise ParseError."""
    with pytest.raises(ParseError) as exc_info:
        parse_date_cutoff("not-a-date")
    assert "Invalid date format" in str(exc_info.value)

    with pytest.raises(ParseError) as exc_info:
        parse_date_cutoff("2024/01/15")
    assert "Invalid date format" in str(exc_info.value)
