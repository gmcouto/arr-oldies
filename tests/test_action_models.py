"""Tests for action domain models, validation, and JSON serialization."""

from datetime import UTC, datetime

from arr_oldies.actions.models import (
    ActionItem,
    ActionPlan,
    ActionResult,
    ActionType,
    ExecutionReport,
)
from arr_oldies.inventory.models import HistoryStatus, MediaInventoryItem, MediaType
from arr_oldies.models import InstanceType


def create_sample_item(item_id: str = "radarr:1") -> MediaInventoryItem:
    """Create a valid MediaInventoryItem for testing."""
    return MediaInventoryItem(
        id=item_id,
        instance_name="radarr-main",
        instance_type=InstanceType.RADARR,
        media_type=MediaType.MOVIE,
        title="Test Movie",
        year=2020,
        movie_id=10,
        movie_file_id=100,
        file_path="/movies/Test Movie (2020)/Test Movie.mkv",
        size_bytes=1024 * 1024 * 500,
        import_date=datetime(2023, 1, 1, tzinfo=UTC),
        history_status=HistoryStatus.IMPORTED,
    )


def test_action_types_enum() -> None:
    """Verify ActionType enum values."""
    assert ActionType.DELETE == "delete"
    assert ActionType.UNMONITOR == "unmonitor"
    assert ActionType.UNMONITOR_EPISODE == "unmonitor_episode"
    assert ActionType.REMOVE == "remove"


def test_action_item_model() -> None:
    """Verify ActionItem instantiation and fields."""
    item = create_sample_item()
    action_item = ActionItem(item=item, action_types=[ActionType.DELETE, ActionType.UNMONITOR])
    assert action_item.item.id == "radarr:1"
    assert action_item.action_types == [ActionType.DELETE, ActionType.UNMONITOR]


def test_action_plan_model() -> None:
    """Verify ActionPlan instantiation, defaults, and dictionary export."""
    item = create_sample_item()
    action_item = ActionItem(item=item, action_types=[ActionType.DELETE])
    plan = ActionPlan(
        target_actions=[ActionType.DELETE],
        items=[action_item],
        total_items=1,
        total_size_bytes=524288000,
        instances_breakdown={"radarr-main": 1},
        dry_run=True,
    )
    assert plan.dry_run is True
    assert plan.total_items == 1
    assert plan.total_size_bytes == 524288000
    assert plan.instances_breakdown == {"radarr-main": 1}

    dumped = plan.model_dump()
    assert dumped["target_actions"] == ["delete"]
    assert len(dumped["items"]) == 1


def test_action_result_model() -> None:
    """Verify ActionResult success and error cases."""
    res_success = ActionResult(
        item_id="radarr:1",
        instance_name="radarr-main",
        action_type=ActionType.DELETE,
        success=True,
        freed_bytes=1000,
    )
    assert res_success.success is True
    assert res_success.error_message is None

    res_failure = ActionResult(
        item_id="radarr:2",
        instance_name="radarr-main",
        action_type=ActionType.UNMONITOR,
        success=False,
        freed_bytes=0,
        error_message="HTTP 500 Internal Server Error",
    )
    assert res_failure.success is False
    assert res_failure.error_message == "HTTP 500 Internal Server Error"


def test_execution_report_model() -> None:
    """Verify ExecutionReport aggregation and timezone handling."""
    res = ActionResult(
        item_id="radarr:1",
        instance_name="radarr-main",
        action_type=ActionType.DELETE,
        success=True,
        freed_bytes=500,
    )
    report = ExecutionReport(
        mode="execute",
        target_actions=[ActionType.DELETE],
        total_attempted=1,
        successful_count=1,
        failed_count=0,
        total_freed_bytes=500,
        results=[res],
        duration_seconds=1.25,
    )
    assert report.mode == "execute"
    assert report.total_attempted == 1
    assert report.successful_count == 1
    assert report.failed_count == 0
    assert report.total_freed_bytes == 500
    assert report.executed_at.tzinfo == UTC
    assert report.duration_seconds == 1.25
