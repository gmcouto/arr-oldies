"""Unit tests for reporting formatters."""

from datetime import UTC, datetime

from arr_oldies.inventory.models import MediaInventoryItem, MediaType
from arr_oldies.models import InstanceType
from arr_oldies.reporting.formatters import (
    format_age_markup,
    format_audio_languages,
    format_instance_badge,
    format_media_title,
    format_size,
    get_age_color,
)


def test_format_size() -> None:
    """Verify IEC binary unit conversion across magnitudes."""
    assert format_size(-100) == "0 B"
    assert format_size(0) == "0 B"
    assert format_size(500) == "500 B"
    assert format_size(1023) == "1023 B"
    assert format_size(1024) == "1.00 KiB"
    assert format_size(1536) == "1.50 KiB"
    assert format_size(1048576) == "1.00 MiB"
    assert format_size(15500000000) == "14.44 GiB"
    assert format_size(2199023255552) == "2.00 TiB"


def test_get_age_color() -> None:
    """Verify age color tiers and legacy status."""
    assert get_age_color(10, is_legacy=True) == "dim"
    assert get_age_color(800, is_legacy=True) == "dim"
    assert get_age_color(800, is_legacy=False) == "bold red"
    assert get_age_color(730, is_legacy=False) == "bold red"
    assert get_age_color(729, is_legacy=False) == "yellow"
    assert get_age_color(365, is_legacy=False) == "yellow"
    assert get_age_color(364, is_legacy=False) == "cyan"
    assert get_age_color(180, is_legacy=False) == "cyan"
    assert get_age_color(179, is_legacy=False) == "green"
    assert get_age_color(0, is_legacy=False) == "green"


def test_format_age_markup() -> None:
    """Verify age markup with context years, months, and legacy flags."""
    # 800 days -> >=365 days, 800/365.25 = 2.19 -> 2.2y, red
    res_800 = format_age_markup(800)
    assert "[bold red]" in res_800
    assert "800 d (2.2y)" in res_800

    # 400 days -> 400/365.25 = 1.095 -> 1.1y, yellow
    res_400 = format_age_markup(400)
    assert "[yellow]" in res_400
    assert "400 d (1.1y)" in res_400

    # 200 days -> 200/30.4 = 6.578 -> 6.6m, cyan
    res_200 = format_age_markup(200)
    assert "[cyan]" in res_200
    assert "200 d (6.6m)" in res_200

    # 10 days -> 10 d, green
    res_10 = format_age_markup(10)
    assert "[green]" in res_10
    assert "10 d" in res_10

    # Legacy item
    res_leg = format_age_markup(500, is_legacy=True)
    assert "[dim]" in res_leg
    assert "(legacy)" in res_leg


def test_format_instance_badge() -> None:
    """Verify Radarr and Sonarr instance badges."""
    radarr_badge = format_instance_badge("radarr-4k", InstanceType.RADARR)
    assert "[bold cyan]radarr-4k[/bold cyan]" == radarr_badge

    sonarr_badge = format_instance_badge("sonarr-anime", InstanceType.SONARR)
    assert "[bold magenta]sonarr-anime[/bold magenta]" == sonarr_badge


def test_format_audio_languages() -> None:
    """Verify audio language tag coloring and empty fallback."""
    assert format_audio_languages([]) == "[dim]None[/dim]"
    assert format_audio_languages(["English"]) == "[green]English[/green]"
    assert format_audio_languages(["eng"]) == "[green]eng[/green]"
    assert format_audio_languages(["Japanese"]) == "[blue]Japanese[/blue]"
    assert format_audio_languages(["ja"]) == "[blue]ja[/blue]"
    assert format_audio_languages(["French"]) == "[white]French[/white]"

    multi = format_audio_languages(["English", "Japanese", "German"])
    assert multi == "[green]English[/green], [blue]Japanese[/blue], [white]German[/white]"


def test_format_media_title() -> None:
    """Verify movie and episode title formatting with markup escaping."""
    movie = MediaInventoryItem(
        id="radarr:1",
        instance_name="radarr",
        instance_type=InstanceType.RADARR,
        media_type=MediaType.MOVIE,
        title="The Matrix [red]",
        year=1999,
        file_path="/movies/Matrix.mkv",
        size_bytes=1000,
        import_date=datetime(2023, 1, 1, tzinfo=UTC),
        resolution="1080p",
    )
    movie_title = format_media_title(movie)
    assert r"[bold white]The Matrix \[red][/bold white]" in movie_title
    assert "[dim](1999)[/dim]" in movie_title
    assert "[dim]· 1080p[/dim]" in movie_title

    episode = MediaInventoryItem(
        id="sonarr:1",
        instance_name="sonarr",
        instance_type=InstanceType.SONARR,
        media_type=MediaType.EPISODE,
        title="Breaking Bad [bold]",
        season_number=1,
        episode_numbers=[1],
        formatted_episode="S01E01",
        episode_title="Pilot [green]",
        file_path="/tv/BB_S01E01.mkv",
        size_bytes=1000,
        import_date=datetime(2023, 1, 1, tzinfo=UTC),
        resolution="2160p",
    )
    ep_title = format_media_title(episode)
    assert r"[bold white]Breaking Bad \[bold][/bold white]" in ep_title
    assert "[bold yellow]S01E01[/bold yellow]" in ep_title
    assert r'"Pilot \[green\]"' in ep_title or r'"Pilot \[green]"' in ep_title
    assert "[dim]· 2160p[/dim]" in ep_title

