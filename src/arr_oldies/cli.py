"""Typer CLI application entrypoint and commands."""

import asyncio
import sys
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from arr_oldies import __version__
from arr_oldies.actions import (
    ActionExecutor,
    ActionType,
    prompt_confirmation,
    render_dry_run_table,
    render_execution_report_table,
)
from arr_oldies.api.fetcher import MultiInstanceFetcher
from arr_oldies.config import load_config

from arr_oldies.console import (
    print_debug,
    print_error,
    render_banner,
    render_validation_table,
    stderr_console,
    stdout_console,
)
from arr_oldies.constants import EXIT_CONFIG_ERROR, EXIT_PROBE_ERROR, EXIT_SUCCESS
from arr_oldies.exceptions import ConfigError, InstanceError, ParseError
from arr_oldies.inventory.correlator import HistoryCorrelator
from arr_oldies.inventory.engine import InventoryEngine
from arr_oldies.inventory.models import (
    InventoryFilter,
    MediaType,
    SortDirection,
    SortKey,
)
from arr_oldies.inventory.parser import parse_age_cutoff, parse_date_cutoff, parse_size
from arr_oldies.prober import probe_all_instances
from arr_oldies.reporting import (
    OutputFormat,
    export_inventory_json,
    render_inventory_table,
    render_summary_panel,
)
from arr_oldies.targeting import resolve_target_instances

app = typer.Typer(
    name="arr-oldies",
    help="Audit and clean stale media across Radarr and Sonarr instances.",
    no_args_is_help=False,
    add_completion=False,
)

console = Console()


def version_callback(value: bool) -> None:
    """Print the version string and exit cleanly."""
    if value:
        typer.echo(f"arr-oldies {__version__}")
        raise typer.Exit(code=EXIT_SUCCESS)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    config: Annotated[
        Path | None,
        typer.Option(
            "--config",
            "-c",
            help="Path to configuration YAML file.",
            exists=False,
            dir_okay=False,
            readable=True,
        ),
    ] = None,
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-v",
            help="Enable verbose / debug diagnostic logging to stderr.",
        ),
    ] = False,
    version: Annotated[
        bool | None,
        typer.Option(
            "--version",
            help="Show version and exit.",
            callback=version_callback,
            is_eager=True,
        ),
    ] = None,
) -> None:
    """Arr-Oldies CLI application entrypoint."""
    ctx.ensure_object(dict)
    ctx.obj["config"] = config
    ctx.obj["verbose"] = verbose

    if ctx.invoked_subcommand is None:
        render_banner()
        raise typer.Exit(code=EXIT_SUCCESS)


@app.command("validate-config")
def validate_config_command(
    ctx: typer.Context,
    radarr: Annotated[
        bool,
        typer.Option("--radarr", help="Validate only Radarr instances."),
    ] = False,
    sonarr: Annotated[
        bool,
        typer.Option("--sonarr", help="Validate only Sonarr instances."),
    ] = False,
    instance: Annotated[
        list[str] | None,
        typer.Option(
            "-i",
            "--instance",
            help="Specific instance name(s) to validate (repeatable).",
        ),
    ] = None,
    config: Annotated[
        Path | None,
        typer.Option(
            "--config",
            "-c",
            help="Path to configuration YAML file (overrides global option).",
        ),
    ] = None,
) -> None:
    """Verify configuration syntax, connectivity, and authentication for all or targeted instances."""
    global_config: Path | None = ctx.obj.get("config") if ctx.obj else None
    effective_config = config or global_config
    verbose: bool = ctx.obj.get("verbose", False) if ctx.obj else False

    print_debug(f"Loading configuration from {effective_config or 'default discovery'}", verbose)

    # 1. Load and parse configuration
    try:
        app_config = load_config(effective_config)
    except ConfigError as exc:
        print_error(str(exc))
        raise typer.Exit(code=EXIT_CONFIG_ERROR) from exc

    # 2. Resolve target instances
    try:
        target_instances = resolve_target_instances(
            app_config,
            radarr=radarr,
            sonarr=sonarr,
            instance_names=instance,
        )
    except InstanceError as exc:
        print_error(str(exc))
        raise typer.Exit(code=EXIT_CONFIG_ERROR) from exc

    print_debug(f"Targeting {len(target_instances)} instance(s) for health probing", verbose)

    # 3. Concurrent async probe
    probe_results = asyncio.run(probe_all_instances(target_instances))

    # 4. Render results table to stdout
    table = render_validation_table(probe_results)
    console.print(table)

    # 5. Determine exit code per D-13
    all_successful = all(res.success for res in probe_results)
    if all_successful:
        raise typer.Exit(code=EXIT_SUCCESS)
    else:
        raise typer.Exit(code=EXIT_PROBE_ERROR)


@app.command("scan")
def scan_command(
    ctx: typer.Context,
    radarr: Annotated[
        bool,
        typer.Option("--radarr", help="Target only Radarr instances."),
    ] = False,
    sonarr: Annotated[
        bool,
        typer.Option("--sonarr", help="Target only Sonarr instances."),
    ] = False,
    instance: Annotated[
        list[str] | None,
        typer.Option(
            "-i",
            "--instance",
            help="Specific instance name(s) to target (repeatable).",
        ),
    ] = None,
    config: Annotated[
        Path | None,
        typer.Option(
            "--config",
            "-c",
            help="Path to configuration YAML file (overrides global option).",
        ),
    ] = None,
    media_type: Annotated[
        MediaType | None,
        typer.Option("--type", "-t", help="Filter by media type ('movie' or 'episode')."),
    ] = None,
    audio_lang: Annotated[
        list[str] | None,
        typer.Option(
            "--audio-lang",
            "-l",
            help="Filter by audio language (repeatable, e.g. -l ja -l en).",
        ),
    ] = None,
    min_size: Annotated[
        str | None,
        typer.Option("--min-size", help="Minimum file size (e.g. '500MB', '2GB')."),
    ] = None,
    max_size: Annotated[
        str | None,
        typer.Option("--max-size", help="Maximum file size (e.g. '10GB')."),
    ] = None,
    older_than: Annotated[
        str | None,
        typer.Option(
            "--older-than",
            "--age",
            help="Minimum age cutoff (e.g. '30d', '6m', '1y').",
        ),
    ] = None,
    newer_than: Annotated[
        str | None,
        typer.Option("--newer-than", help="Maximum age cutoff (e.g. '1y', '90d')."),
    ] = None,
    before: Annotated[
        str | None,
        typer.Option("--before", help="Imported before date (e.g. '2023-01-01')."),
    ] = None,
    after: Annotated[
        str | None,
        typer.Option("--after", help="Imported after date (e.g. '2024-01-01')."),
    ] = None,
    legacy: Annotated[
        bool,
        typer.Option(
            "--legacy",
            "--legacy-only",
            help="Filter only legacy unindexed items (no history).",
        ),
    ] = False,
    history: Annotated[
        bool,
        typer.Option(
            "--history",
            "--history-only",
            help="Filter only items with verified history records.",
        ),
    ] = False,
    sort: Annotated[
        SortKey,
        typer.Option(
            "--sort",
            "-s",
            help="Sort field ('import_date', 'grab_date', 'size', 'title', 'age').",
        ),
    ] = SortKey.IMPORT_DATE,
    sort_dir: Annotated[
        SortDirection,
        typer.Option(
            "--sort-dir",
            "--order",
            help="Sort direction ('asc', 'desc').",
        ),
    ] = SortDirection.ASC,
    limit: Annotated[
        int | None,
        typer.Option(
            "--limit",
            "-n",
            min=1,
            help="Limit output to top N items.",
        ),
    ] = None,
    format: Annotated[
        OutputFormat,
        typer.Option(
            "--format",
            "-f",
            help="Output format ('table' or 'json').",
        ),
    ] = OutputFormat.TABLE,
    summary: Annotated[
        bool,
        typer.Option(
            "--summary/--no-summary",
            help="Display summary metrics panel (table mode only).",
        ),
    ] = True,
) -> None:
    """Audit and visualize downloaded media files sorted by age across Radarr and Sonarr instances."""
    global_config: Path | None = ctx.obj.get("config") if ctx.obj else None
    effective_config = config or global_config
    verbose: bool = ctx.obj.get("verbose", False) if ctx.obj else False

    print_debug(f"Loading configuration from {effective_config or 'default discovery'}", verbose)

    # 1. Load configuration
    try:
        app_config = load_config(effective_config)
    except ConfigError as exc:
        print_error(str(exc))
        raise typer.Exit(code=EXIT_CONFIG_ERROR) from exc

    # 2. Resolve target instances
    try:
        target_instances = resolve_target_instances(
            app_config,
            radarr=radarr,
            sonarr=sonarr,
            instance_names=instance,
        )
    except InstanceError as exc:
        print_error(str(exc))
        raise typer.Exit(code=EXIT_CONFIG_ERROR) from exc

    # 3. Parse filter arguments
    try:
        min_size_bytes = parse_size(min_size) if min_size else None
        max_size_bytes = parse_size(max_size) if max_size else None
        min_age_days = parse_age_cutoff(older_than) if older_than else None
        max_age_days = parse_age_cutoff(newer_than) if newer_than else None
        before_date = parse_date_cutoff(before) if before else None
        after_date = parse_date_cutoff(after) if after else None
    except ParseError as exc:
        print_error(str(exc))
        raise typer.Exit(code=EXIT_CONFIG_ERROR) from exc

    criteria = InventoryFilter(
        media_types=[media_type] if media_type else None,
        audio_langs=audio_lang,
        min_size_bytes=min_size_bytes,
        max_size_bytes=max_size_bytes,
        min_age_days=min_age_days,
        max_age_days=max_age_days,
        before_date=before_date,
        after_date=after_date,
        legacy_only=legacy,
        history_only=history,
    )

    # 4. Fetch library and history data concurrently
    fetcher = MultiInstanceFetcher()
    if format == OutputFormat.TABLE:
        with stderr_console.status(
            "[bold cyan]Scanning instances and fetching history records...[/bold cyan]"
        ):
            results = asyncio.run(fetcher.fetch_all_instances_data(target_instances))
    else:
        results = asyncio.run(fetcher.fetch_all_instances_data(target_instances))

    successful_results = [res for res in results if res.success and res.data]
    failed_results = [res for res in results if not res.success]

    if not successful_results:
        error_details = "; ".join(f"{r.instance_name}: {r.error_message}" for r in failed_results)
        print_error(f"All target instances failed to fetch data: {error_details}")
        raise typer.Exit(code=EXIT_PROBE_ERROR)

    for failed in failed_results:
        stderr_console.print(
            f"[bold yellow]Warning:[/bold yellow] Failed to fetch from '{failed.instance_name}': {failed.error_message}"
        )

    # 5. Correlate media items
    correlator = HistoryCorrelator()
    all_items = []
    for res in successful_results:
        if res.data:
            items = correlator.correlate_instance(res.data)
            all_items.extend(items)
    total_scanned_count = len(all_items)

    # 6. Filter inventory
    engine = InventoryEngine()
    filtered_items = engine.filter_inventory(all_items, criteria)

    # 7. Sort inventory
    sorted_items = engine.sort_inventory(filtered_items, sort_key=sort, direction=sort_dir)

    # 8. Generate summary metrics
    inventory_summary = engine.generate_summary(sorted_items)

    # 9. Apply limit
    display_items = sorted_items[:limit] if limit else sorted_items

    # 10. Render output
    if format == OutputFormat.JSON:
        json_output = export_inventory_json(
            items=sorted_items,
            summary=inventory_summary,
            target_instances=[inst.name for inst in target_instances],
            total_scanned=total_scanned_count,
            limit=limit,
            sort_key=sort,
            sort_direction=sort_dir,
        )
        typer.echo(json_output)
    else:
        if not sorted_items:
            stdout_console.print(
                "[yellow]No media items matched the specified criteria.[/yellow]"
            )
        else:
            table = render_inventory_table(
                display_items,
                total_count=len(sorted_items),
                limit=limit,
            )
            stdout_console.print(table)

        if summary:
            panel = render_summary_panel(
                inventory_summary,
                displayed_items_count=len(display_items),
                displayed_size_bytes=sum(i.size_bytes for i in display_items),
            )
            stdout_console.print(panel)

    raise typer.Exit(code=EXIT_SUCCESS)


@app.command("clean")
def clean_command(
    ctx: typer.Context,
    delete: Annotated[
        bool,
        typer.Option("--delete", help="Delete target media file(s) via *arr API."),
    ] = False,
    unmonitor: Annotated[
        bool,
        typer.Option("--unmonitor", help="Unmonitor movie or entire TV show."),
    ] = False,
    unmonitor_episode: Annotated[
        bool,
        typer.Option("--unmonitor-episode", help="Unmonitor specific episode(s)."),
    ] = False,
    remove: Annotated[
        bool,
        typer.Option("--remove", help="Remove complete movie/series entry from library."),
    ] = False,
    execute: Annotated[
        bool,
        typer.Option("--execute", help="Execute write operations (default is dry-run simulation)."),
    ] = False,
    yes: Annotated[
        bool,
        typer.Option("-y", "--yes", help="Bypass interactive confirmation prompt."),
    ] = False,
    radarr: Annotated[
        bool,
        typer.Option("--radarr", help="Target only Radarr instances."),
    ] = False,
    sonarr: Annotated[
        bool,
        typer.Option("--sonarr", help="Target only Sonarr instances."),
    ] = False,
    instance: Annotated[
        list[str] | None,
        typer.Option(
            "-i",
            "--instance",
            help="Specific instance name(s) to target (repeatable).",
        ),
    ] = None,
    config: Annotated[
        Path | None,
        typer.Option(
            "--config",
            "-c",
            help="Path to configuration YAML file (overrides global option).",
        ),
    ] = None,
    media_type: Annotated[
        MediaType | None,
        typer.Option("--type", "-t", help="Filter by media type ('movie' or 'episode')."),
    ] = None,
    audio_lang: Annotated[
        list[str] | None,
        typer.Option(
            "--audio-lang",
            "-l",
            help="Filter by audio language (repeatable, e.g. -l ja -l en).",
        ),
    ] = None,
    min_size: Annotated[
        str | None,
        typer.Option("--min-size", help="Minimum file size (e.g. '500MB', '2GB')."),
    ] = None,
    max_size: Annotated[
        str | None,
        typer.Option("--max-size", help="Maximum file size (e.g. '10GB')."),
    ] = None,
    older_than: Annotated[
        str | None,
        typer.Option(
            "--older-than",
            "--age",
            help="Minimum age cutoff (e.g. '30d', '6m', '1y').",
        ),
    ] = None,
    newer_than: Annotated[
        str | None,
        typer.Option("--newer-than", help="Maximum age cutoff (e.g. '1y', '90d')."),
    ] = None,
    before: Annotated[
        str | None,
        typer.Option("--before", help="Imported before date (e.g. '2023-01-01')."),
    ] = None,
    after: Annotated[
        str | None,
        typer.Option("--after", help="Imported after date (e.g. '2024-01-01')."),
    ] = None,
    legacy: Annotated[
        bool,
        typer.Option(
            "--legacy",
            "--legacy-only",
            help="Filter only legacy unindexed items (no history).",
        ),
    ] = False,
    history: Annotated[
        bool,
        typer.Option(
            "--history",
            "--history-only",
            help="Filter only items with verified history records.",
        ),
    ] = False,
    sort: Annotated[
        SortKey,
        typer.Option(
            "--sort",
            "-s",
            help="Sort field ('import_date', 'grab_date', 'size', 'title', 'age').",
        ),
    ] = SortKey.IMPORT_DATE,
    sort_dir: Annotated[
        SortDirection,
        typer.Option(
            "--sort-dir",
            "--order",
            help="Sort direction ('asc', 'desc').",
        ),
    ] = SortDirection.ASC,
    limit: Annotated[
        int | None,
        typer.Option(
            "--limit",
            "-n",
            min=1,
            help="Limit target items to top N.",
        ),
    ] = None,
    format: Annotated[
        OutputFormat,
        typer.Option(
            "--format",
            "-f",
            help="Output format ('table' or 'json').",
        ),
    ] = OutputFormat.TABLE,
) -> None:
    """Safely execute targeted actions (delete, unmonitor, remove) on media items with dry-run protection."""
    actions: list[ActionType] = []
    if delete:
        actions.append(ActionType.DELETE)
    if unmonitor:
        actions.append(ActionType.UNMONITOR)
    if unmonitor_episode:
        actions.append(ActionType.UNMONITOR_EPISODE)
    if remove:
        actions.append(ActionType.REMOVE)

    if not actions:
        print_error(
            "No action specified. Please provide at least one action flag: "
            "--delete, --unmonitor, --unmonitor-episode, --remove"
        )
        raise typer.Exit(code=EXIT_CONFIG_ERROR)

    global_config: Path | None = ctx.obj.get("config") if ctx.obj else None
    effective_config = config or global_config
    verbose: bool = ctx.obj.get("verbose", False) if ctx.obj else False

    print_debug(f"Loading configuration from {effective_config or 'default discovery'}", verbose)

    # 1. Load configuration
    try:
        app_config = load_config(effective_config)
    except ConfigError as exc:
        print_error(str(exc))
        raise typer.Exit(code=EXIT_CONFIG_ERROR) from exc

    # 2. Resolve target instances
    try:
        target_instances = resolve_target_instances(
            app_config,
            radarr=radarr,
            sonarr=sonarr,
            instance_names=instance,
        )
    except InstanceError as exc:
        print_error(str(exc))
        raise typer.Exit(code=EXIT_CONFIG_ERROR) from exc

    # 3. Parse filter arguments
    try:
        min_size_bytes = parse_size(min_size) if min_size else None
        max_size_bytes = parse_size(max_size) if max_size else None
        min_age_days = parse_age_cutoff(older_than) if older_than else None
        max_age_days = parse_age_cutoff(newer_than) if newer_than else None
        before_date = parse_date_cutoff(before) if before else None
        after_date = parse_date_cutoff(after) if after else None
    except ParseError as exc:
        print_error(str(exc))
        raise typer.Exit(code=EXIT_CONFIG_ERROR) from exc

    criteria = InventoryFilter(
        media_types=[media_type] if media_type else None,
        audio_langs=audio_lang,
        min_size_bytes=min_size_bytes,
        max_size_bytes=max_size_bytes,
        min_age_days=min_age_days,
        max_age_days=max_age_days,
        before_date=before_date,
        after_date=after_date,
        legacy_only=legacy,
        history_only=history,
    )

    # 4. Fetch library and history data
    fetcher = MultiInstanceFetcher()
    if format == OutputFormat.TABLE:
        with stderr_console.status(
            "[bold cyan]Scanning instances and fetching history records...[/bold cyan]"
        ):
            results = asyncio.run(fetcher.fetch_all_instances_data(target_instances))
    else:
        results = asyncio.run(fetcher.fetch_all_instances_data(target_instances))

    successful_results = [res for res in results if res.success and res.data]
    failed_results = [res for res in results if not res.success]

    if not successful_results:
        error_details = "; ".join(f"{r.instance_name}: {r.error_message}" for r in failed_results)
        print_error(f"All target instances failed to fetch data: {error_details}")
        raise typer.Exit(code=EXIT_PROBE_ERROR)

    for failed in failed_results:
        stderr_console.print(
            f"[bold yellow]Warning:[/bold yellow] Failed to fetch from '{failed.instance_name}': {failed.error_message}"
        )

    # 5. Correlate media items
    correlator = HistoryCorrelator()
    all_items = []
    for res in successful_results:
        if res.data:
            items = correlator.correlate_instance(res.data)
            all_items.extend(items)

    # 6. Filter & Sort inventory
    engine = InventoryEngine()
    filtered_items = engine.filter_inventory(all_items, criteria)
    sorted_items = engine.sort_inventory(filtered_items, sort_key=sort, direction=sort_dir)
    target_items = sorted_items[:limit] if limit else sorted_items

    # 7. Build ActionPlan
    executor = ActionExecutor()
    plan = executor.build_plan(items=target_items, actions=actions, dry_run=not execute)

    # 8. Dry-Run Mode (ACT-01)
    if not execute:
        if format == OutputFormat.JSON:
            typer.echo(executor.export_plan_json(plan))
        else:
            stdout_console.print(render_dry_run_table(plan))
            stdout_console.print(
                "\n[bold yellow]DRY-RUN MODE:[/] No changes were made. "
                "Re-run with [bold cyan]--execute[/bold cyan] to apply mutations."
            )
        raise typer.Exit(code=EXIT_SUCCESS)

    # 9. Execute Mode (ACT-06, ACT-07)
    if not yes:
        if not sys.stdin.isatty():
            stderr_console.print(
                "[bold red]Error:[/bold red] Interactive confirmation required in execute mode. "
                "Use --yes for automated / non-interactive execution."
            )
            raise typer.Exit(code=EXIT_PROBE_ERROR)

        confirmed = prompt_confirmation(
            plan,
            stderr_console if format == OutputFormat.JSON else stdout_console,
        )
        if not confirmed:
            if format == OutputFormat.JSON:
                stderr_console.print("[yellow]Operation aborted by user. No changes were made.[/yellow]")
            else:
                stdout_console.print("[yellow]Operation aborted by user. No changes were made.[/yellow]")
            raise typer.Exit(code=EXIT_SUCCESS)

    report = asyncio.run(executor.execute_plan(plan, target_instances))

    if format == OutputFormat.JSON:
        typer.echo(executor.export_report_json(report))
    else:
        stdout_console.print(render_execution_report_table(report))

    raise typer.Exit(code=EXIT_SUCCESS)


if __name__ == "__main__":
    app()

