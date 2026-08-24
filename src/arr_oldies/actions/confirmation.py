"""Rich confirmation warning modals, dry-run simulation tables, and interactive prompt helpers."""

import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from arr_oldies.actions.models import ActionPlan, ExecutionReport
from arr_oldies.reporting.formatters import (
    format_age_markup,
    format_instance_badge,
    format_media_title,
    format_size,
)


def render_confirmation_panel(plan: ActionPlan) -> Panel:
    """Construct a high-contrast warning panel summarizing pending destructive mutations."""
    grid = Table.grid(expand=True, padding=(0, 2))
    grid.add_column(style="bold yellow", justify="left")
    grid.add_column(style="bold white", justify="right")

    actions_str = ", ".join(
        f"[bold red]{act.value.upper()}[/bold red]" for act in plan.target_actions
    )
    grid.add_row("Actions to Perform:", actions_str or "[dim]None[/dim]")
    grid.add_row("Total Items Affected:", f"{plan.total_items:,} items")
    grid.add_row(
        "Potential Space to be Freed:",
        f"[bold green]{format_size(plan.total_size_bytes)}[/bold green]",
    )

    breakdown_str = (
        ", ".join(f"{inst}: {cnt:,}" for inst, cnt in plan.instances_breakdown.items())
        if plan.instances_breakdown
        else "None"
    )
    grid.add_row("Instances Breakdown:", breakdown_str)

    return Panel(
        grid,
        title="[bold bright_white on red] WARNING: DESTRUCTIVE MUTATION REQUESTED [/bold bright_white on red]",
        border_style="red",
        box=box.ROUNDED,
    )


def render_dry_run_table(plan: ActionPlan) -> Table:
    """Construct a Rich table presenting proposed actions in dry-run simulation mode."""
    table = Table(
        title="[bold yellow]Arr-Oldies Dry-Run Action Simulation[/bold yellow]",
        box=box.ROUNDED,
        header_style="bold bright_white on grey23",
        show_header=True,
    )

    table.add_column("#", style="dim", justify="right", width=4)
    table.add_column("Instance", style="bold", no_wrap=True)
    table.add_column("Type", style="dim", width=8)
    table.add_column("Title / Episode", style="bold white", min_width=25)
    table.add_column("Size", style="bright_yellow", justify="right")
    table.add_column("Age", justify="right")
    table.add_column("Proposed Actions", style="bold cyan")

    for idx, action_item in enumerate(plan.items):
        item = action_item.item
        actions_str = ", ".join(
            f"[bold cyan]{act.value.upper()}[/bold cyan]" for act in action_item.action_types
        )
        table.add_row(
            str(idx + 1),
            format_instance_badge(item.instance_name, item.instance_type),
            item.media_type.value,
            format_media_title(item),
            format_size(item.size_bytes),
            format_age_markup(item.age_days, item.is_legacy),
            actions_str,
        )

    return table


def render_execution_report_table(report: ExecutionReport) -> Table:
    """Construct a Rich table presenting the results of executed mutations."""
    table = Table(
        title="[bold green]Arr-Oldies Execution Report[/bold green]",
        box=box.ROUNDED,
        header_style="bold bright_white on grey23",
        show_header=True,
    )

    table.add_column("#", style="dim", justify="right", width=4)
    table.add_column("Item ID", style="bold", no_wrap=True)
    table.add_column("Instance", style="bold", no_wrap=True)
    table.add_column("Action", style="cyan", no_wrap=True)
    table.add_column("Status", justify="center", no_wrap=True)
    table.add_column("Freed Space", style="bright_yellow", justify="right")
    table.add_column("Details / Error", style="white")

    for idx, result in enumerate(report.results):
        status_str = (
            "[bold green]SUCCESS[/bold green]" if result.success else "[bold red]FAILED[/bold red]"
        )
        freed_str = (
            format_size(result.freed_bytes) if result.success and result.freed_bytes > 0 else "-"
        )
        details_str = (
            f"[red]{result.error_message}[/red]" if result.error_message else "[dim]Completed[/dim]"
        )

        table.add_row(
            str(idx + 1),
            result.item_id,
            result.instance_name,
            result.action_type.value.upper(),
            status_str,
            freed_str,
            details_str,
        )

    table.caption = (
        f"[bold]Summary:[/] {report.successful_count:,} succeeded, "
        f"{report.failed_count:,} failed | Total space freed: "
        f"[bold green]{format_size(report.total_freed_bytes)}[/bold green] "
        f"in {report.duration_seconds:.2f}s"
    )
    return table


def prompt_confirmation(plan: ActionPlan, console: Console) -> bool:
    """Render warning panel to console and prompt user for explicit interactive confirmation."""
    panel = render_confirmation_panel(plan)
    console.print(panel)
    return typer.confirm(
        f"Are you sure you want to proceed with executing mutations on {plan.total_items} items?",
        default=False,
    )
