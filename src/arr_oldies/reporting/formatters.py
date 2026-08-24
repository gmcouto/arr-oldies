"""Formatting helpers for sizes, age tiers, instance badges, and media metadata."""

from rich.markup import escape

from arr_oldies.inventory.models import MediaInventoryItem, MediaType
from arr_oldies.models import InstanceType


def format_size(bytes_val: int) -> str:
    """Format integer bytes into IEC binary human-readable string (e.g. '14.25 GiB', '850.50 MiB')."""
    if bytes_val < 0:
        return "0 B"
    if bytes_val < 1024:
        return f"{bytes_val} B"

    units = ["KiB", "MiB", "GiB", "TiB", "PiB"]
    val = float(bytes_val)
    unit_idx = -1

    while val >= 1024.0 and unit_idx < len(units) - 1:
        val /= 1024.0
        unit_idx += 1

    return f"{val:.2f} {units[unit_idx]}"


def get_age_color(age_days: int, is_legacy: bool = False) -> str:
    """Return Rich color style based on age tiers and legacy status."""
    if is_legacy:
        return "dim"
    if age_days >= 730:  # 2+ years
        return "bold red"
    if age_days >= 365:  # 1-2 years
        return "yellow"
    if age_days >= 180:  # 6-12 months
        return "cyan"
    return "green"  # < 6 months


def format_age_markup(age_days: int, is_legacy: bool = False) -> str:
    """Format age into styled string with years/months context and legacy tag."""
    color = get_age_color(age_days, is_legacy)
    if age_days >= 365:
        years = age_days / 365.25
        formatted = f"{age_days:,} d ({years:.1f}y)"
    elif age_days >= 30:
        months = age_days / 30.4
        formatted = f"{age_days:,} d ({months:.1f}m)"
    else:
        formatted = f"{age_days} d"

    if is_legacy:
        return f"[{color}]{formatted} [dim italic](legacy)[/dim italic][/{color}]"
    return f"[{color}]{formatted}[/{color}]"


def format_instance_badge(instance_name: str, instance_type: InstanceType) -> str:
    """Render instance name badge styled by instance type."""
    if instance_type == InstanceType.RADARR:
        return f"[bold cyan]{instance_name}[/bold cyan]"
    return f"[bold magenta]{instance_name}[/bold magenta]"


def format_audio_languages(languages: list[str]) -> str:
    """Render audio language tags or fallback to None."""
    if not languages:
        return "[dim]None[/dim]"

    badges: list[str] = []
    for lang in languages:
        clean = lang.strip()
        if not clean:
            continue
        lower_clean = clean.lower()
        if lower_clean in ("english", "eng", "en"):
            badges.append(f"[green]{clean}[/green]")
        elif lower_clean in ("japanese", "jpn", "ja"):
            badges.append(f"[blue]{clean}[/blue]")
        else:
            badges.append(f"[white]{clean}[/white]")

    return ", ".join(badges) if badges else "[dim]None[/dim]"


def format_media_title(item: MediaInventoryItem) -> str:
    """Format movie or TV episode title with year and season/episode info with escaped markup."""
    escaped_title = escape(item.title)
    if item.media_type == MediaType.MOVIE:
        year_str = f" [dim]({item.year})[/dim]" if item.year else ""
        quality_str = f" [dim]· {item.resolution}[/dim]" if item.resolution else ""
        return f"[bold white]{escaped_title}[/bold white]{year_str}{quality_str}"

    ep_str = f" [bold yellow]{item.formatted_episode}[/bold yellow]" if item.formatted_episode else ""
    ep_title = f' [dim]"{escape(item.episode_title)}"[/dim]' if item.episode_title else ""
    quality_str = f" [dim]· {item.resolution}[/dim]" if item.resolution else ""
    return f"[bold white]{escaped_title}[/bold white]{ep_str}{ep_title}{quality_str}"
