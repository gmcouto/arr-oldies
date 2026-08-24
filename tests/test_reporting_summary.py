"""Unit tests for summary metrics panel rendering."""

from datetime import UTC, datetime

from rich.console import Console

from arr_oldies.inventory.models import InventorySummary
from arr_oldies.reporting.summary import render_summary_panel


def test_summary_panel_populated() -> None:
    """Verify summary panel with fully populated statistics."""
    summary = InventorySummary(
        total_items=120,
        total_size_bytes=450_000_000_000,
        movie_count=40,
        episode_count=80,
        legacy_count=5,
        oldest_import_date=datetime(2020, 1, 1, tzinfo=UTC),
        newest_import_date=datetime(2024, 1, 1, tzinfo=UTC),
        instances_breakdown={"radarr-hd": 40, "sonarr-tv": 80},
    )

    panel = render_summary_panel(
        summary=summary,
        displayed_items_count=10,
        displayed_size_bytes=50_000_000_000,
    )

    console = Console(record=True, width=120)
    console.print(panel)
    output = console.export_text()

    assert "Scan Summary & Storage Metrics" in output
    assert "120 (40 movies, 80 eps)" in output
    assert "419.10 GiB" in output
    assert "2020-01-01 to 2024-01-01 (4.0y)" in output
    assert "46.57 GiB" in output
    assert "10 files" in output
    assert "5 items" in output
    assert "radarr-hd: 40, sonarr-tv: 80" in output


def test_summary_panel_empty() -> None:
    """Verify summary panel handles empty inventory gracefully without crashing."""
    summary = InventorySummary()
    panel = render_summary_panel(summary)

    console = Console(record=True, width=120)
    console.print(panel)
    output = console.export_text()

    assert "Scan Summary & Storage Metrics" in output
    assert "0 (0 movies, 0 eps)" in output
    assert "0 B" in output
    assert "N/A" in output
    assert "None" in output


def test_summary_panel_default_space_reclamation() -> None:
    """Verify potential space freed defaults to total size and total items when not explicitly overridden."""
    summary = InventorySummary(
        total_items=25,
        total_size_bytes=100_000_000_000,
        movie_count=25,
        episode_count=0,
        legacy_count=0,
        oldest_import_date=datetime(2023, 6, 1, tzinfo=UTC),
        newest_import_date=datetime(2023, 12, 1, tzinfo=UTC),
        instances_breakdown={"radarr-hd": 25},
    )

    panel = render_summary_panel(summary)
    console = Console(record=True, width=120)
    console.print(panel)
    output = console.export_text()

    assert "93.13 GiB" in output
    assert "(25 files)" in output
