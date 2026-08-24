"""Rich terminal presentation, validation table rendering, banner, and console helpers."""

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from arr_oldies import __version__
from arr_oldies.models import ProbeResult

# Standard output and error consoles
stdout_console = Console()
stderr_console = Console(stderr=True)


def mask_secret(secret_str: str, visible_prefix: int = 4) -> str:
    """Mask a sensitive credential string while preserving an optional prefix.

    Args:
        secret_str: Raw secret string.
        visible_prefix: Number of characters to leave unmasked at start if long enough.

    Returns:
        Masked string representation (e.g. 'abcd****' or '****').
    """
    if len(secret_str) > visible_prefix + 4:
        return f"{secret_str[:visible_prefix]}****"
    return "****"


def render_validation_table(results: list[ProbeResult]) -> Table:
    """Construct a high-contrast Rich table summarizing health probe results."""
    table = Table(
        title="Instance Validation Results",
        box=box.ROUNDED,
        header_style="bold cyan",
        show_header=True,
    )

    table.add_column("Instance", style="bold cyan", no_wrap=True)
    table.add_column("Type", style="magenta")
    table.add_column("Base URL", style="blue")
    table.add_column("Version", style="white")
    table.add_column("Latency", style="yellow", justify="right")
    table.add_column("Status", style="bold")

    for res in results:
        version_str = res.version or "Unknown"
        latency_str = f"{res.latency_ms:.1f} ms"

        if res.success:
            status_markup = "[bold green]✓ [OK][/bold green]"
        else:
            err_msg = f" [dim]({res.error_message})[/dim]" if res.error_message else ""
            status_markup = f"[bold red]✗ [FAIL][/bold red]{err_msg}"

        table.add_row(
            res.instance_name,
            res.instance_type.value,
            res.url,
            version_str,
            latency_str,
            status_markup,
        )

    return table


def render_banner() -> None:
    """Print the styled welcome banner and command guide for bare CLI invocations."""
    banner_text = (
        f"[bold cyan]Arr-Oldies[/bold cyan] [dim]v{__version__}[/dim]\n"
        "[white]Audit and clean stale media across Radarr and Sonarr instances.[/white]\n\n"
        "[bold yellow]Commands:[/bold yellow]\n"
        "  [bold green]validate-config[/bold green]  Verify configuration syntax, connectivity, and authentication\n"
        "  [bold green]scan[/bold green]             Audit media library and sort downloads by age [dim](Phase 4)[/dim]\n\n"
        "[bold yellow]Usage Examples:[/bold yellow]\n"
        "  [dim]$[/dim] arr-oldies validate-config\n"
        "  [dim]$[/dim] arr-oldies validate-config --radarr\n"
        "  [dim]$[/dim] arr-oldies validate-config -i radarr-hd -i sonarr-tv\n"
        "  [dim]$[/dim] arr-oldies --config /path/to/config.yaml validate-config\n\n"
        "Run [bold cyan]arr-oldies --help[/bold cyan] or [bold cyan]arr-oldies <command> --help[/bold cyan] for full options."
    )
    panel = Panel(
        banner_text,
        title="[bold blue]Welcome to Arr-Oldies[/bold blue]",
        border_style="bright_blue",
        box=box.ROUNDED,
    )
    stdout_console.print(panel)


def print_error(message: str) -> None:
    """Output error diagnostic to stderr."""
    stderr_console.print(f"[bold red]Error:[/bold red] {message}")


def print_debug(message: str, verbose: bool = False) -> None:
    """Output debug diagnostic to stderr when verbose is active."""
    if verbose:
        stderr_console.print(f"[dim][DEBUG] {message}[/dim]")
