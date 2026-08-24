"""Unit tests for Rich inventory table rendering."""

from datetime import UTC, datetime

from rich.console import Console

from arr_oldies.inventory.models import MediaInventoryItem, MediaType
from arr_oldies.models import InstanceType
from arr_oldies.reporting.table import render_inventory_table


def _make_movie(
    item_id: str = "radarr:1",
    instance_name: str = "radarr-hd",
    title: str = "Inception",
    year: int = 2010,
    size_bytes: int = 15_000_000_000,
    age_days: int = 400,
    is_legacy: bool = False,
    languages: list[str] | None = None,
) -> MediaInventoryItem:
    return MediaInventoryItem(
        id=item_id,
        instance_name=instance_name,
        instance_type=InstanceType.RADARR,
        media_type=MediaType.MOVIE,
        title=title,
        year=year,
        file_path=f"/movies/{title}.mkv",
        size_bytes=size_bytes,
        import_date=datetime(2023, 1, 15, tzinfo=UTC),
        age_days=age_days,
        is_legacy=is_legacy,
        audio_languages=languages if languages is not None else ["English"],
        resolution="1080p",
    )


def _make_episode(
    item_id: str = "sonarr:1",
    instance_name: str = "sonarr-tv",
    title: str = "Attack on Titan",
    season: int = 1,
    episode_numbers: list[int] | None = None,
    formatted_episode: str = "S01E01",
    episode_title: str = "To You, in 2000 Years",
    size_bytes: int = 1_500_000_000,
    age_days: int = 800,
    is_legacy: bool = False,
    languages: list[str] | None = None,
) -> MediaInventoryItem:
    return MediaInventoryItem(
        id=item_id,
        instance_name=instance_name,
        instance_type=InstanceType.SONARR,
        media_type=MediaType.EPISODE,
        title=title,
        season_number=season,
        episode_numbers=episode_numbers or [1],
        formatted_episode=formatted_episode,
        episode_title=episode_title,
        file_path=f"/tv/{title}/{formatted_episode}.mkv",
        size_bytes=size_bytes,
        import_date=datetime(2022, 5, 20, tzinfo=UTC),
        age_days=age_days,
        is_legacy=is_legacy,
        audio_languages=languages if languages is not None else ["Japanese", "English"],
        resolution="1080p",
    )


def test_table_structure_and_columns() -> None:
    """Verify table has expected 8 columns with proper header titles."""
    table = render_inventory_table([])
    assert len(table.columns) == 8
    header_names = [col.header for col in table.columns]
    assert header_names == [
        "#",
        "Instance",
        "Type",
        "Title / Episode",
        "Size",
        "Import Date",
        "Age",
        "Audio",
    ]


def test_table_rendering_empty() -> None:
    """Verify empty item list renders cleanly without error."""
    table = render_inventory_table([])
    assert table.row_count == 0

    console = Console(record=True, width=120)
    console.print(table)
    output = console.export_text()
    assert "Arr-Oldies Media Inventory" in output


def test_table_rendering_items() -> None:
    """Verify table row counts, formatted values, and rich output."""
    items = [
        _make_movie(title="Inception", age_days=400),
        _make_episode(title="Attack on Titan", formatted_episode="S01E01-E02", is_legacy=True),
    ]
    table = render_inventory_table(items)
    assert table.row_count == 2

    console = Console(record=True, width=140)
    console.print(table)
    output = console.export_text()

    assert "Inception" in output
    assert "Attack on Titan" in output
    assert "S01E01-E02" in output
    assert "radarr-hd" in output
    assert "sonarr-tv" in output
    assert "(legacy)" in output
    assert "13.97 GiB" in output
    assert "1.40 GiB" in output


def test_table_limit_caption() -> None:
    """Verify table caption is added when limit slices total results."""
    items = [_make_movie()]
    # Total count matches items -> no caption
    table_no_cap = render_inventory_table(items, total_count=1, limit=10)
    assert table_no_cap.caption is None

    # Total count > items -> caption present
    table_cap = render_inventory_table(items, total_count=50, limit=1)
    assert table_cap.caption == "[dim]Showing top 1 of 50 items[/dim]"


def test_table_rendering_narrow_terminal_and_multiple_languages() -> None:
    """Verify media titles and episodes are not collapsed or hidden at various console widths."""
    items = [
        _make_movie(
            title="Oppenheimer",
            year=2023,
            size_bytes=20_000_000_000,
            age_days=365,
            languages=["Portuguese", "English"],
        ),
        _make_episode(
            title="Demon Slayer: Kimetsu no Yaiba",
            season=5,
            formatted_episode="S05E01",
            episode_title="To Defeat Muzan Kibutsuji",
            size_bytes=3_000_000_000,
            age_days=728,
            languages=["Portuguese", "Japanese"],
        ),
    ]
    table = render_inventory_table(items)

    for width in [80, 100, 120, 140, 160]:
        console = Console(record=True, width=width)
        console.print(table)
        output = console.export_text()
        assert "Oppenheimer" in output, f"Oppenheimer missing at width {width}"
        assert "Demon Slayer" in output, f"Demon Slayer missing at width {width}"
        assert "S05E01" in output, f"S05E01 missing at width {width}"
