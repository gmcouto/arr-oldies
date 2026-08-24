"""Typer CLI application entrypoint and commands."""

import asyncio
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from arr_oldies import __version__
from arr_oldies.config import load_config
from arr_oldies.console import print_debug, print_error, render_banner, render_validation_table
from arr_oldies.constants import EXIT_CONFIG_ERROR, EXIT_PROBE_ERROR, EXIT_SUCCESS
from arr_oldies.exceptions import ConfigError, InstanceError
from arr_oldies.prober import probe_all_instances
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


if __name__ == "__main__":
    app()
