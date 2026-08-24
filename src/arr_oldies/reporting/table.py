"""Rich table rendering for media inventory scan results."""

from rich import box
from rich.table import Table

from arr_oldies.inventory.models import MediaInventoryItem, MediaType
from arr_oldies.reporting.formatters import (
    format_age_markup,
    format_audio_languages,
    format_instance_badge,
    format_media_title,
    format_size,
)


def render_inventory_table(
    items: list[MediaInventoryItem],
    total_count: int | None = None,
    limit: int | None = None,
) -> Table:
    """Construct a high-contrast Rich table summarizing media inventory items."""
    table = Table(
        title="[bold cyan]Arr-Oldies Media Inventory[/bold cyan]",
        box=box.ROUNDED,
        header_style="bold bright_white on grey23",
        show_header=True,
        show_lines=False,
    )

    table.add_column("#", style="dim", justify="right", no_wrap=True)
    table.add_column("Instance", style="bold", no_wrap=True)
    table.add_column("Type", style="dim", no_wrap=True)
    table.add_column("Title / Episode", style="bold white", min_width=25, overflow="ellipsis")
    table.add_column("Size", style="bright_yellow", justify="right", no_wrap=True)
    table.add_column("Import Date", style="white", justify="center", no_wrap=True)
    table.add_column("Age", justify="right", no_wrap=True)
    table.add_column("Audio", style="white", no_wrap=True)

    for idx, item in enumerate(items, start=1):
        type_str = (
            "[blue]Movie[/blue]"
            if item.media_type == MediaType.MOVIE
            else "[purple]Episode[/purple]"
        )
        inst_badge = format_instance_badge(item.instance_name, item.instance_type)
        title_str = format_media_title(item)
        size_str = format_size(item.size_bytes)
        import_str = item.import_date.strftime("%Y-%m-%d")
        age_str = format_age_markup(item.age_days, item.is_legacy)
        lang_str = format_audio_languages(item.audio_languages)

        table.add_row(
            str(idx),
            inst_badge,
            type_str,
            title_str,
            size_str,
            import_str,
            age_str,
            lang_str,
        )

    if limit and total_count and total_count > len(items):
        table.caption = f"[dim]Showing top {len(items):,} of {total_count:,} items[/dim]"

    return table
