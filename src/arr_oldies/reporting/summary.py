"""Summary panel component detailing storage metrics and space reclamation."""

from rich import box
from rich.panel import Panel
from rich.table import Table

from arr_oldies.inventory.models import InventorySummary
from arr_oldies.reporting.formatters import format_size


def render_summary_panel(
    summary: InventorySummary,
    displayed_items_count: int | None = None,
    displayed_size_bytes: int | None = None,
) -> Panel:
    """Construct a high-contrast Rich summary panel detailing scan metrics."""
    grid = Table.grid(expand=True, padding=(0, 2))
    grid.add_column(style="bold cyan", justify="left")
    grid.add_column(style="bold white", justify="right")
    grid.add_column(style="bold cyan", justify="left")
    grid.add_column(style="bold white", justify="right")

    # Row 1: Item counts and Total Volume
    grid.add_row(
        "Total Media Items:",
        f"{summary.total_items:,} ({summary.movie_count:,} movies, {summary.episode_count:,} eps)",
        "Total Storage:",
        f"[bright_yellow]{format_size(summary.total_size_bytes)}[/bright_yellow]",
    )

    # Row 2: Date Range and Space Reclamation
    if summary.oldest_import_date and summary.newest_import_date:
        span_days = max(0, (summary.newest_import_date - summary.oldest_import_date).days)
        span_years = span_days / 365.25
        date_span_str = (
            f"{summary.oldest_import_date.strftime('%Y-%m-%d')} to "
            f"{summary.newest_import_date.strftime('%Y-%m-%d')} ({span_years:.1f}y)"
        )
    else:
        date_span_str = "N/A"

    reclaim_bytes = (
        displayed_size_bytes if displayed_size_bytes is not None else summary.total_size_bytes
    )
    reclaim_count = (
        displayed_items_count if displayed_items_count is not None else summary.total_items
    )
    reclaim_str = f"[bold green]{format_size(reclaim_bytes)}[/bold green] ({reclaim_count:,} files)"

    grid.add_row(
        "Date Range Spanned:",
        date_span_str,
        "Potential Space Freed:",
        reclaim_str,
    )

    # Row 3: Legacy Items and Instance Breakdown
    instances_str = (
        ", ".join(f"{name}: {cnt:,}" for name, cnt in summary.instances_breakdown.items()) or "None"
    )
    grid.add_row(
        "Legacy (No History):",
        f"{summary.legacy_count:,} items",
        "Instances Breakdown:",
        instances_str,
    )

    return Panel(
        grid,
        title="[bold bright_white on blue] Scan Summary & Storage Metrics [/bold bright_white on blue]",
        border_style="bright_blue",
        box=box.ROUNDED,
    )
