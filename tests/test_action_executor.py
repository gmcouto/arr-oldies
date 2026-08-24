"""Unit tests for ActionExecutor simulation planning and execution engine."""

import json
from datetime import UTC, datetime

import pytest
import respx
from pydantic import SecretStr

from arr_oldies.actions.executor import ActionExecutor
from arr_oldies.actions.models import ActionItem, ActionPlan, ActionType
from arr_oldies.inventory.models import HistoryStatus, MediaInventoryItem, MediaType

from arr_oldies.models import InstanceConfig, InstanceType



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


@pytest.mark.asyncio
@respx.mock
async def test_execute_plan_deletions_and_unmonitoring() -> None:
    """Verify execute_plan executes unmonitor before delete, deduplicates unmonitors, and calculates freed space."""
    route_radarr_unmonitor = respx.put("http://radarr.local:7878/api/v3/movie/editor").respond(status_code=202)
    route_radarr_delete = respx.delete("http://radarr.local:7878/api/v3/moviefile/50").respond(status_code=200)

    route_sonarr_unmonitor = respx.put("http://sonarr.local:8989/api/v3/series/editor").respond(status_code=202)
    route_sonarr_delete1 = respx.delete("http://sonarr.local:8989/api/v3/episodefile/200").respond(status_code=204)

    items = create_test_items()
    # Add a second episode from the same series to test deduplication
    ep2 = MediaInventoryItem(
        id="sonarr:2",
        instance_name="sonarr-main",
        instance_type=InstanceType.SONARR,
        media_type=MediaType.EPISODE,
        title="Breaking Bad",
        season_number=1,
        episode_numbers=[2],
        formatted_episode="S01E02",
        series_id=20,
        episode_file_id=201,
        episode_ids=[1002],
        file_path="/tv/Breaking Bad/Season 01/S01E02.mkv",
        size_bytes=3 * 1024 * 1024 * 1024,  # 3 GiB
        import_date=datetime(2023, 1, 2, tzinfo=UTC),
        history_status=HistoryStatus.IMPORTED,
    )
    route_sonarr_delete2 = respx.delete("http://sonarr.local:8989/api/v3/episodefile/201").respond(status_code=204)
    items.append(ep2)

    instances = [
        InstanceConfig(
            name="radarr-main",
            type=InstanceType.RADARR,
            url="http://radarr.local:7878",
            api_key=SecretStr("key1"),
        ),
        InstanceConfig(
            name="sonarr-main",
            type=InstanceType.SONARR,
            url="http://sonarr.local:8989",
            api_key=SecretStr("key2"),
        ),
    ]

    executor = ActionExecutor()
    plan = executor.build_plan(items=items, actions=[ActionType.UNMONITOR, ActionType.DELETE], dry_run=False)

    report = await executor.execute_plan(plan, instances)

    assert report.mode == "execute"
    assert report.total_attempted == 6  # 3 unmonitors (1 movie, 2 eps with deduplicated series unmonitor) + 3 deletes
    assert report.successful_count == 6
    assert report.failed_count == 0
    assert report.total_freed_bytes == 15 * 1024 * 1024 * 1024

    # Verify series unmonitor was called only once for Sonarr series 20
    assert route_sonarr_unmonitor.call_count == 1
    assert route_radarr_unmonitor.call_count == 1
    assert route_radarr_delete.called
    assert route_sonarr_delete1.called
    assert route_sonarr_delete2.called


@pytest.mark.asyncio
@respx.mock
async def test_execute_plan_unmonitor_episodes() -> None:
    """Verify episode-specific unmonitoring."""
    route_episodes = respx.put("http://sonarr.local:8989/api/v3/episode/monitor").respond(status_code=200)

    items = [create_test_items()[1]]  # episode item
    instances = [
        InstanceConfig(
            name="sonarr-main",
            type=InstanceType.SONARR,
            url="http://sonarr.local:8989",
            api_key=SecretStr("key2"),
        ),
    ]
    executor = ActionExecutor()
    plan = executor.build_plan(items=items, actions=[ActionType.UNMONITOR_EPISODE], dry_run=False)

    report = await executor.execute_plan(plan, instances)
    assert report.successful_count == 1
    assert route_episodes.called



@pytest.mark.asyncio
@respx.mock
async def test_execute_plan_error_resilience() -> None:
    """Verify execute_plan isolates single-item errors and reports both successes and failures."""
    respx.delete("http://radarr.local:7878/api/v3/moviefile/50").respond(status_code=500, text="Disk error")
    respx.delete("http://sonarr.local:8989/api/v3/episodefile/200").respond(status_code=204)

    items = create_test_items()
    instances = [
        InstanceConfig(
            name="radarr-main",
            type=InstanceType.RADARR,
            url="http://radarr.local:7878",
            api_key=SecretStr("key1"),
        ),
        InstanceConfig(
            name="sonarr-main",
            type=InstanceType.SONARR,
            url="http://sonarr.local:8989",
            api_key=SecretStr("key2"),
        ),
    ]

    executor = ActionExecutor()
    plan = executor.build_plan(items=items, actions=[ActionType.DELETE], dry_run=False)

    report = await executor.execute_plan(plan, instances)

    assert report.total_attempted == 2
    assert report.successful_count == 1
    assert report.failed_count == 1
    assert report.total_freed_bytes == 2 * 1024 * 1024 * 1024  # Only Sonarr episode freed bytes

    json_str = executor.export_report_json(report)
    parsed = json.loads(json_str)
    assert parsed["summary"]["successful_count"] == 1
    assert parsed["summary"]["failed_count"] == 1
    assert len(parsed["results"]) == 2


@pytest.mark.asyncio
@respx.mock
async def test_execute_plan_remove_library_entry() -> None:
    """Verify remove action sends DELETE request to movie/series endpoint."""
    route_movie = respx.delete(
        "http://radarr.local:7878/api/v3/movie/5",
        params={"deleteFiles": "true", "addImportExclusion": "false"},
    ).respond(status_code=200)
    route_series = respx.delete(
        "http://sonarr.local:8989/api/v3/series/20",
        params={"deleteFiles": "false", "addImportListExclusion": "false"},
    ).respond(status_code=204)

    items = create_test_items()
    instances = [
        InstanceConfig(
            name="radarr-main",
            type=InstanceType.RADARR,
            url="http://radarr.local:7878",
            api_key=SecretStr("key1"),
        ),
        InstanceConfig(
            name="sonarr-main",
            type=InstanceType.SONARR,
            url="http://sonarr.local:8989",
            api_key=SecretStr("key2"),
        ),
    ]

    # Movie item with DELETE + REMOVE (deleteFiles=True)
    # Series item with REMOVE only (deleteFiles=False)
    executor = ActionExecutor()
    plan = ActionPlan(
        target_actions=[ActionType.REMOVE],
        items=[
            ActionItem(item=items[0], action_types=[ActionType.DELETE, ActionType.REMOVE]),
            ActionItem(item=items[1], action_types=[ActionType.REMOVE]),
        ],
        total_items=2,
        total_size_bytes=items[0].size_bytes + items[1].size_bytes,
        instances_breakdown={"radarr-main": 1, "sonarr-main": 1},
        dry_run=False,
    )

    report = await executor.execute_plan(plan, instances)
    assert report.successful_count == 2
    assert route_movie.called
    assert route_series.called
    assert report.total_freed_bytes == items[0].size_bytes


