"""Unit tests for InventoryEngine filtering, deterministic sorting, and summary metrics."""

from datetime import UTC, datetime

import pytest

from arr_oldies.inventory.engine import InventoryEngine
from arr_oldies.inventory.models import (
    HistoryStatus,
    InventoryFilter,
    MediaInventoryItem,
    MediaType,
    SortDirection,
    SortKey,
)
from arr_oldies.models import InstanceType


@pytest.fixture
def sample_items() -> list[MediaInventoryItem]:
    return [
        MediaInventoryItem(
            id="radarr-main:1",
            instance_name="radarr-main",
            instance_type=InstanceType.RADARR,
            media_type=MediaType.MOVIE,
            title="Old Anime Movie",
            file_path="/movies/Old Anime Movie/Old Anime Movie.mkv",
            size_bytes=1000000000,  # 1GB
            audio_languages=["Japanese"],
            import_date=datetime(2021, 1, 1, 0, 0, 0, tzinfo=UTC),
            grab_date=datetime(2020, 12, 31, 23, 0, 0, tzinfo=UTC),
            age_days=1000,
            has_history=True,
            is_legacy=False,
            history_status=HistoryStatus.GRABBED_AND_IMPORTED,
        ),
        MediaInventoryItem(
            id="sonarr-tv:2",
            instance_name="sonarr-tv",
            instance_type=InstanceType.SONARR,
            media_type=MediaType.EPISODE,
            title="New Drama Show",
            file_path="/tv/New Drama Show/S01E01.mkv",
            size_bytes=5000000000,  # 5GB
            audio_languages=["English", "French"],
            import_date=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
            grab_date=datetime(2023, 12, 30, 10, 0, 0, tzinfo=UTC),
            age_days=50,
            has_history=True,
            is_legacy=False,
            history_status=HistoryStatus.GRABBED_AND_IMPORTED,
        ),
        MediaInventoryItem(
            id="radarr-4k:3",
            instance_name="radarr-4k",
            instance_type=InstanceType.RADARR,
            media_type=MediaType.MOVIE,
            title="Legacy Movie",
            file_path="/movies/Legacy Movie/Legacy Movie.mkv",
            size_bytes=20000000000,  # 20GB
            audio_languages=["English"],
            import_date=datetime(2020, 1, 1, 0, 0, 0, tzinfo=UTC),
            grab_date=None,
            age_days=1400,
            has_history=False,
            is_legacy=True,
            history_status=HistoryStatus.LEGACY,
        ),
    ]


def test_filter_by_audio_language(sample_items: list[MediaInventoryItem]):
    """Verify filtering by audio language matches canonical names and ISO codes."""
    engine = InventoryEngine()

    # Code match: "ja" -> Japanese
    filtered_ja = engine.filter_inventory(sample_items, InventoryFilter(audio_langs=["ja"]))
    assert len(filtered_ja) == 1
    assert filtered_ja[0].title == "Old Anime Movie"

    # Name synonym match: "japanese"
    filtered_jpn = engine.filter_inventory(sample_items, InventoryFilter(audio_langs=["japanese"]))
    assert len(filtered_jpn) == 1
    assert filtered_jpn[0].title == "Old Anime Movie"

    # ISO-3 match: "fre"
    filtered_fr = engine.filter_inventory(sample_items, InventoryFilter(audio_langs=["fre"]))
    assert len(filtered_fr) == 1
    assert filtered_fr[0].title == "New Drama Show"

    # Non-matching language: "de"
    filtered_de = engine.filter_inventory(sample_items, InventoryFilter(audio_langs=["de"]))
    assert len(filtered_de) == 0


def test_filter_by_size_bounds(sample_items: list[MediaInventoryItem]):
    """Verify filtering by minimum and maximum file size in bytes."""
    engine = InventoryEngine()

    # min_size >= 2GB (2,000,000,000)
    filtered_min = engine.filter_inventory(sample_items, InventoryFilter(min_size_bytes=2000000000))
    assert len(filtered_min) == 2
    assert {i.title for i in filtered_min} == {"New Drama Show", "Legacy Movie"}

    # max_size <= 2GB
    filtered_max = engine.filter_inventory(sample_items, InventoryFilter(max_size_bytes=2000000000))
    assert len(filtered_max) == 1
    assert filtered_max[0].title == "Old Anime Movie"

    # Range: 2GB to 10GB
    filtered_range = engine.filter_inventory(
        sample_items,
        InventoryFilter(min_size_bytes=2000000000, max_size_bytes=10000000000),
    )
    assert len(filtered_range) == 1
    assert filtered_range[0].title == "New Drama Show"


def test_filter_by_age_bounds(sample_items: list[MediaInventoryItem]):
    """Verify filtering by minimum and maximum age in days."""
    engine = InventoryEngine()

    # min_age >= 500 days
    filtered_old = engine.filter_inventory(sample_items, InventoryFilter(min_age_days=500))
    assert len(filtered_old) == 2
    assert {i.title for i in filtered_old} == {"Old Anime Movie", "Legacy Movie"}

    # max_age <= 100 days
    filtered_recent = engine.filter_inventory(sample_items, InventoryFilter(max_age_days=100))
    assert len(filtered_recent) == 1
    assert filtered_recent[0].title == "New Drama Show"


def test_filter_by_date_bounds(sample_items: list[MediaInventoryItem]):
    """Verify filtering by before_date and after_date cutoffs."""
    engine = InventoryEngine()

    # before 2022-01-01
    filtered_before = engine.filter_inventory(
        sample_items,
        InventoryFilter(before_date=datetime(2022, 1, 1, 0, 0, 0, tzinfo=UTC)),
    )
    assert len(filtered_before) == 2
    assert {i.title for i in filtered_before} == {"Legacy Movie", "Old Anime Movie"}

    # after 2022-01-01
    filtered_after = engine.filter_inventory(
        sample_items,
        InventoryFilter(after_date=datetime(2022, 1, 1, 0, 0, 0, tzinfo=UTC)),
    )
    assert len(filtered_after) == 1
    assert filtered_after[0].title == "New Drama Show"


def test_filter_by_media_type_and_instance(sample_items: list[MediaInventoryItem]):
    """Verify filtering by MediaType and instance name."""
    engine = InventoryEngine()

    # Only movies
    filtered_movies = engine.filter_inventory(sample_items, InventoryFilter(media_types=[MediaType.MOVIE]))
    assert len(filtered_movies) == 2
    assert {i.title for i in filtered_movies} == {"Old Anime Movie", "Legacy Movie"}

    # Only episodes
    filtered_eps = engine.filter_inventory(sample_items, InventoryFilter(media_types=[MediaType.EPISODE]))
    assert len(filtered_eps) == 1
    assert filtered_eps[0].title == "New Drama Show"

    # Instance name (case-insensitive)
    filtered_inst = engine.filter_inventory(sample_items, InventoryFilter(instance_names=["RADARR-MAIN"]))
    assert len(filtered_inst) == 1
    assert filtered_inst[0].title == "Old Anime Movie"


def test_filter_by_legacy_and_history_flags(sample_items: list[MediaInventoryItem]):
    """Verify filtering by legacy_only and history_only flags."""
    engine = InventoryEngine()

    # Legacy only
    filtered_legacy = engine.filter_inventory(sample_items, InventoryFilter(legacy_only=True))
    assert len(filtered_legacy) == 1
    assert filtered_legacy[0].title == "Legacy Movie"

    # History only
    filtered_history = engine.filter_inventory(sample_items, InventoryFilter(history_only=True))
    assert len(filtered_history) == 2
    assert {i.title for i in filtered_history} == {"Old Anime Movie", "New Drama Show"}


def test_sort_inventory_keys_and_directions(sample_items: list[MediaInventoryItem]):
    """Verify deterministic sorting by import_date, grab_date, size, title, and age."""
    engine = InventoryEngine()

    # 1. Oldest import date (default ASC)
    sorted_import_asc = engine.sort_inventory(sample_items, SortKey.IMPORT_DATE, SortDirection.ASC)
    assert [i.title for i in sorted_import_asc] == ["Legacy Movie", "Old Anime Movie", "New Drama Show"]

    # 2. Newest import date (DESC)
    sorted_import_desc = engine.sort_inventory(sample_items, SortKey.IMPORT_DATE, SortDirection.DESC)
    assert [i.title for i in sorted_import_desc] == ["New Drama Show", "Old Anime Movie", "Legacy Movie"]

    # 3. Oldest grab date (fallback to import_date for legacy items without grab_date)
    sorted_grab = engine.sort_inventory(sample_items, SortKey.GRAB_DATE, SortDirection.ASC)
    assert [i.title for i in sorted_grab] == ["Legacy Movie", "Old Anime Movie", "New Drama Show"]

    # 4. Size descending
    sorted_size_desc = engine.sort_inventory(sample_items, SortKey.SIZE, SortDirection.DESC)
    assert [i.title for i in sorted_size_desc] == ["Legacy Movie", "New Drama Show", "Old Anime Movie"]

    # 5. Title ascending
    sorted_title = engine.sort_inventory(sample_items, SortKey.TITLE, SortDirection.ASC)
    assert [i.title for i in sorted_title] == ["Legacy Movie", "New Drama Show", "Old Anime Movie"]

    # 6. Age ascending (youngest to oldest)
    sorted_age_asc = engine.sort_inventory(sample_items, SortKey.AGE, SortDirection.ASC)
    assert [i.title for i in sorted_age_asc] == ["New Drama Show", "Old Anime Movie", "Legacy Movie"]


def test_generate_summary_metrics(sample_items: list[MediaInventoryItem]):
    """Verify summary metrics calculation across mixed items."""
    engine = InventoryEngine()
    summary = engine.generate_summary(sample_items)

    assert summary.total_items == 3
    assert summary.total_size_bytes == 26000000000
    assert summary.movie_count == 2
    assert summary.episode_count == 1
    assert summary.legacy_count == 1
    assert summary.oldest_import_date == datetime(2020, 1, 1, 0, 0, 0, tzinfo=UTC)
    assert summary.newest_import_date == datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)
    assert summary.oldest_grab_date == datetime(2020, 12, 31, 23, 0, 0, tzinfo=UTC)
    assert summary.instances_breakdown == {
        "radarr-main": 1,
        "sonarr-tv": 1,
        "radarr-4k": 1,
    }


def test_generate_summary_empty():
    """Verify summary metrics calculation for an empty collection."""
    engine = InventoryEngine()
    summary = engine.generate_summary([])

    assert summary.total_items == 0
    assert summary.total_size_bytes == 0
    assert summary.movie_count == 0
    assert summary.episode_count == 0
    assert summary.legacy_count == 0
    assert summary.oldest_import_date is None
    assert summary.newest_import_date is None
    assert summary.oldest_grab_date is None
    assert summary.instances_breakdown == {}
