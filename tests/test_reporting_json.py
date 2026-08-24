"""Unit tests for structured JSON export serializer."""

import json
from datetime import UTC, datetime

from arr_oldies.inventory.models import (
    HistoryStatus,
    InventorySummary,
    MediaInventoryItem,
    MediaType,
    SortDirection,
    SortKey,
)
from arr_oldies.models import InstanceType
from arr_oldies.reporting.json_export import build_json_payload, export_inventory_json


def _make_sample_item(
    item_id: str = "radarr:101",
    instance_name: str = "radarr-hd",
    title: str = "The Matrix",
    year: int = 1999,
    size_bytes: int = 14_500_000_000,
    age_days: int = 450,
) -> MediaInventoryItem:
    return MediaInventoryItem(
        id=item_id,
        instance_name=instance_name,
        instance_type=InstanceType.RADARR,
        media_type=MediaType.MOVIE,
        title=title,
        year=year,
        file_path=f"/movies/{title} ({year})/{title}.mkv",
        size_bytes=size_bytes,
        import_date=datetime(2023, 5, 10, 12, 0, 0, tzinfo=UTC),
        grab_date=datetime(2023, 5, 10, 11, 0, 0, tzinfo=UTC),
        age_days=age_days,
        has_history=True,
        is_legacy=False,
        history_status=HistoryStatus.GRABBED_AND_IMPORTED,
        audio_languages=["English", "Japanese"],
        resolution="1080p",
    )


def test_build_json_payload_structure() -> None:
    """Verify dictionary structure, metadata keys, summary metrics, and item records."""
    items = [
        _make_sample_item(item_id="radarr:1", title="Movie 1", size_bytes=10_000_000_000),
        _make_sample_item(item_id="radarr:2", title="Movie 2", size_bytes=20_000_000_000),
    ]
    summary = InventorySummary(
        total_items=2,
        total_size_bytes=30_000_000_000,
        movie_count=2,
        episode_count=0,
        legacy_count=0,
        oldest_import_date=datetime(2023, 1, 1, tzinfo=UTC),
        newest_import_date=datetime(2023, 6, 1, tzinfo=UTC),
        instances_breakdown={"radarr-hd": 2},
    )

    payload = build_json_payload(
        items=items,
        summary=summary,
        target_instances=["radarr-hd"],
        total_scanned=10,
        limit=1,
        sort_key=SortKey.SIZE,
        sort_direction=SortDirection.DESC,
    )

    # Metadata checks
    meta = payload["metadata"]
    assert meta["target_instances"] == ["radarr-hd"]
    assert meta["total_scanned_items"] == 10
    assert meta["total_matched_items"] == 2
    assert meta["displayed_items"] == 1
    assert meta["limit"] == 1
    assert meta["sort_key"] == "size"
    assert meta["sort_direction"] == "desc"

    # Summary checks
    sum_data = payload["summary"]
    assert sum_data["total_items"] == 2
    assert sum_data["total_size_bytes"] == 30_000_000_000
    assert sum_data["total_size_human"] == "27.94 GiB"
    assert sum_data["potential_space_freed_bytes"] == 10_000_000_000
    assert sum_data["potential_space_freed_human"] == "9.31 GiB"
    assert sum_data["date_range_spanned_days"] == 151
    assert sum_data["instances_breakdown"] == {"radarr-hd": 2}

    # Items checks (sliced to 1 by limit)
    item_records = payload["items"]
    assert len(item_records) == 1
    assert item_records[0]["id"] == "radarr:1"
    assert item_records[0]["title"] == "Movie 1"
    assert item_records[0]["size_human"] == "9.31 GiB"
    assert item_records[0]["instance_type"] == "radarr"
    assert item_records[0]["history_status"] == "grabbed_and_imported"


def test_export_inventory_json_validity_and_purity() -> None:
    """Verify export_inventory_json produces parseable JSON without ANSI escape sequences."""
    items = [_make_sample_item()]
    summary = InventorySummary(
        total_items=1,
        total_size_bytes=14_500_000_000,
        movie_count=1,
        episode_count=0,
        legacy_count=0,
        oldest_import_date=datetime(2023, 5, 10, tzinfo=UTC),
        newest_import_date=datetime(2023, 5, 10, tzinfo=UTC),
        instances_breakdown={"radarr-hd": 1},
    )

    json_str = export_inventory_json(
        items=items,
        summary=summary,
        target_instances=["radarr-hd"],
        total_scanned=1,
    )

    # Must be valid JSON
    parsed = json.loads(json_str)
    assert parsed["metadata"]["total_matched_items"] == 1
    assert len(parsed["items"]) == 1

    # Must not contain ANSI escape codes
    assert "\x1b[" not in json_str
    assert "[bold" not in json_str
