"""Unit tests for confirmation warning modal, action tables, and prompt helpers."""

from datetime import UTC, datetime
from io import StringIO
from unittest.mock import patch

from rich.console import Console

from arr_oldies.actions.confirmation import (
    prompt_confirmation,
    render_confirmation_panel,
    render_dry_run_table,
    render_execution_report_table,
)
from arr_oldies.actions.models import (
    ActionItem,
    ActionPlan,
    ActionResult,
    ActionType,
    ExecutionReport,
)
from arr_oldies.inventory.models import HistoryStatus, MediaInventoryItem, MediaType
from arr_oldies.models import InstanceType


def create_sample_plan() -> ActionPlan:
    """Create a sample ActionPlan for testing rendering."""
    item1 = MediaInventoryItem(
        id="radarr:1",
        instance_name="radarr-main",
        instance_type=InstanceType.RADARR,
        media_type=MediaType.MOVIE,
        title="Gladiator",
        year=2000,
        movie_id=1,
        movie_file_id=10,
        file_path="/movies/Gladiator (2000)/Gladiator.mkv",
        size_bytes=15 * 1024 * 1024 * 1024,
        import_date=datetime(2021, 1, 1, tzinfo=UTC),
        history_status=HistoryStatus.IMPORTED,
    )
    item2 = MediaInventoryItem(
        id="sonarr:1",
        instance_name="sonarr-main",
        instance_type=InstanceType.SONARR,
        media_type=MediaType.EPISODE,
        title="The Wire",
        season_number=1,
        episode_numbers=[1],
        formatted_episode="S01E01",
        series_id=10,
        episode_file_id=100,
        episode_ids=[1001],
        file_path="/tv/The Wire/Season 01/S01E01.mkv",
        size_bytes=1024 * 1024 * 1024,
        import_date=datetime(2022, 1, 1, tzinfo=UTC),
        history_status=HistoryStatus.IMPORTED,
    )
    return ActionPlan(
        target_actions=[ActionType.DELETE, ActionType.UNMONITOR],
        items=[
            ActionItem(item=item1, action_types=[ActionType.DELETE, ActionType.UNMONITOR]),
            ActionItem(item=item2, action_types=[ActionType.DELETE, ActionType.UNMONITOR]),
        ],
        total_items=2,
        total_size_bytes=16 * 1024 * 1024 * 1024,
        instances_breakdown={"radarr-main": 1, "sonarr-main": 1},
        dry_run=True,
    )


def test_render_confirmation_panel() -> None:
    """Verify confirmation panel contains warning title, action names, count, and size."""
    plan = create_sample_plan()
    panel = render_confirmation_panel(plan)

    buf = StringIO()
    console = Console(file=buf, force_terminal=False, color_system=None)
    console.print(panel)
    output = buf.getvalue()

    assert "WARNING: DESTRUCTIVE MUTATION REQUESTED" in output
    assert "DELETE, UNMONITOR" in output
    assert "2 items" in output
    assert "16.00 GiB" in output
    assert "radarr-main: 1" in output
    assert "sonarr-main: 1" in output


def test_render_dry_run_table() -> None:
    """Verify dry-run simulation table renders columns and item rows."""
    plan = create_sample_plan()
    table = render_dry_run_table(plan)

    buf = StringIO()
    console = Console(file=buf, force_terminal=False, color_system=None, width=200)
    console.print(table)
    output = buf.getvalue()

    assert "Arr-Oldies Dry-Run Action Simulation" in output
    assert "Gladiator" in output
    assert "The Wire" in output
    assert "15.00 GiB" in output
    assert "1.00 GiB" in output
    assert "DELETE, UNMONITOR" in output


def test_render_execution_report_table() -> None:
    """Verify execution report table renders status badges, freed space, and caption."""
    report = ExecutionReport(
        mode="execute",
        target_actions=[ActionType.DELETE],
        total_attempted=2,
        successful_count=1,
        failed_count=1,
        total_freed_bytes=15 * 1024 * 1024 * 1024,
        results=[
            ActionResult(
                item_id="radarr:1",
                instance_name="radarr-main",
                action_type=ActionType.DELETE,
                success=True,
                freed_bytes=15 * 1024 * 1024 * 1024,
            ),
            ActionResult(
                item_id="sonarr:1",
                instance_name="sonarr-main",
                action_type=ActionType.DELETE,
                success=False,
                freed_bytes=0,
                error_message="HTTP 500 Disk Full",
            ),
        ],
        duration_seconds=2.45,
    )
    table = render_execution_report_table(report)

    buf = StringIO()
    console = Console(file=buf, force_terminal=False, color_system=None, width=200)
    console.print(table)
    output = buf.getvalue()

    assert "Arr-Oldies Execution Report" in output
    assert "SUCCESS" in output
    assert "FAILED" in output
    assert "HTTP 500 Disk Full" in output
    assert "Summary: 1 succeeded, 1 failed" in output
    assert "15.00 GiB" in output
    assert "2.45s" in output



def test_prompt_confirmation_accepted() -> None:
    """Verify prompt_confirmation renders panel and returns True when user confirms."""
    plan = create_sample_plan()
    buf = StringIO()
    console = Console(file=buf, force_terminal=False, color_system=None)

    with patch("typer.confirm", return_value=True) as mock_confirm:
        result = prompt_confirmation(plan, console)
        assert result is True
        mock_confirm.assert_called_once_with(
            "Are you sure you want to proceed with executing mutations on 2 items?",
            default=False,
        )


def test_prompt_confirmation_declined() -> None:
    """Verify prompt_confirmation returns False when user declines."""
    plan = create_sample_plan()
    buf = StringIO()
    console = Console(file=buf, force_terminal=False, color_system=None)

    with patch("typer.confirm", return_value=False) as mock_confirm:
        result = prompt_confirmation(plan, console)
        assert result is False
        mock_confirm.assert_called_once()
