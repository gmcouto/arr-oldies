"""Unit tests for ActionExecutor simulation planning and execution engine."""

import json
from datetime import UTC, datetime

from arr_oldies.actions.executor import ActionExecutor
from arr_oldies.actions.models import ActionPlan, ActionType
from arr_oldies.inventory.models import HistoryStatus, MediaInventoryItem, MediaType
from arr_oldies.models import InstanceType


def create_test_items() -> list[MediaInventoryItem]:
    """Create sample movie and episode items."""
    movie = MediaInventoryItem(
        id="radarr:1",
        instance_name="radarr-main",
        instance_type=InstanceType.RADARR,
        media_type=MediaType.MOVIE,
        title="Inception",
        year=2010,
        movie_id=5,
        movie_file_id=50,
        file_path="/movies/Inception (2010)/Inception.mkv",
        size_bytes=10 * 1024 * 1024 * 1024,  # 10 GiB
        import_date=datetime(2022, 1, 1, tzinfo=UTC),
        history_status=HistoryStatus.IMPORTED,
    )
    episode = MediaInventoryItem(
        id="sonarr:1",
        instance_name="sonarr-main",
        instance_type=InstanceType.SONARR,
        media_type=MediaType.EPISODE,
        title="Breaking Bad",
        season_number=1,
        episode_numbers=[1],
        formatted_episode="S01E01",
        series_id=20,
        episode_file_id=200,
        episode_ids=[1001],
        file_path="/tv/Breaking Bad/Season 01/S01E01.mkv",
        size_bytes=2 * 1024 * 1024 * 1024,  # 2 GiB
        import_date=datetime(2023, 1, 1, tzinfo=UTC),
        history_status=HistoryStatus.IMPORTED,
    )
    return [movie, episode]


def test_build_plan_defaults() -> None:
    """Verify build_plan constructs ActionPlan with dry_run=True, aggregated size, and breakdown."""
    items = create_test_items()
    executor = ActionExecutor()
    plan = executor.build_plan(
        items=items,
        actions=[ActionType.DELETE, ActionType.UNMONITOR],
        dry_run=True,
    )

    assert isinstance(plan, ActionPlan)
    assert plan.dry_run is True
    assert plan.total_items == 2
    assert plan.total_size_bytes == 12 * 1024 * 1024 * 1024
    assert plan.instances_breakdown == {"radarr-main": 1, "sonarr-main": 1}
    assert plan.target_actions == [ActionType.DELETE, ActionType.UNMONITOR]


def test_build_plan_prunes_inapplicable_actions() -> None:
    """Verify unmonitor_episode is pruned on Movie items."""
    items = create_test_items()
    executor = ActionExecutor()
    plan = executor.build_plan(
        items=items,
        actions=[ActionType.DELETE, ActionType.UNMONITOR_EPISODE],
        dry_run=False,
    )

    movie_action_item = next(it for it in plan.items if it.item.media_type == MediaType.MOVIE)
    episode_action_item = next(it for it in plan.items if it.item.media_type == MediaType.EPISODE)

    assert ActionType.UNMONITOR_EPISODE not in movie_action_item.action_types
    assert ActionType.DELETE in movie_action_item.action_types
    assert ActionType.UNMONITOR_EPISODE in episode_action_item.action_types
    assert ActionType.DELETE in episode_action_item.action_types


def test_export_plan_json() -> None:
    """Verify export_plan_json serializes ActionPlan to pure JSON with metadata and human sizes."""
    items = create_test_items()
    executor = ActionExecutor()
    plan = executor.build_plan(
        items=items,
        actions=[ActionType.DELETE],
        dry_run=True,
    )

    json_str = executor.export_plan_json(plan)
    parsed = json.loads(json_str)

    assert parsed["metadata"]["mode"] == "dry-run"
    assert parsed["metadata"]["dry_run"] is True
    assert parsed["summary"]["total_items"] == 2
    assert parsed["summary"]["total_size_bytes"] == 12 * 1024 * 1024 * 1024
    assert "12.00 GiB" in parsed["summary"]["total_size_human"]
    assert len(parsed["items"]) == 2
