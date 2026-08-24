"""Unit tests for MediaInventoryItem, InventoryFilter, and InventorySummary models."""

import json
from datetime import UTC, datetime

from arr_oldies.inventory import (
    HistoryStatus,
    InventoryFilter,
    InventorySummary,
    LanguageEntry,
    LanguageNormalizer,
    MediaInventoryItem,
    MediaType,
    SortDirection,
    SortKey,
    parse_age_cutoff,
    parse_date_cutoff,
    parse_size,
)
from arr_oldies.models import InstanceType


def test_media_inventory_item_instantiation_and_utc_normalization():
    """Verify MediaInventoryItem creation, UTC normalization for naive/aware datetimes, and field defaults."""
    naive_dt = datetime(2024, 1, 1, 12, 0, 0)  # noqa: DTZ001 - testing naive conversion
    item = MediaInventoryItem(
        id="radarr:101",
        instance_name="radarr-main",
        instance_type=InstanceType.RADARR,
        media_type=MediaType.MOVIE,
        title="Interstellar",
        year=2014,
        file_path="/movies/Interstellar (2014)/Interstellar (2014).mkv",
        size_bytes=15000000000,
        audio_languages=["English"],
        import_date=naive_dt,  # Naive should become UTC
        grab_date=datetime(2024, 1, 1, 10, 0, 0, tzinfo=UTC),
        age_days=100,
    )
    assert item.id == "radarr:101"
    assert item.instance_name == "radarr-main"
    assert item.import_date.tzinfo == UTC
    assert item.import_date == datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
    assert item.grab_date == datetime(2024, 1, 1, 10, 0, 0, tzinfo=UTC)
    assert item.has_history is True
    assert item.is_legacy is False
    assert item.history_status == HistoryStatus.IMPORTED
    assert item.episode_numbers == []
    assert item.episode_ids == []
    assert item.relative_path == ""


def test_media_inventory_item_tags_field():
    """Verify MediaInventoryItem default tags=[] and custom tags list handling."""
    item_default = MediaInventoryItem(
        id="radarr:101",
        instance_name="radarr-main",
        instance_type=InstanceType.RADARR,
        media_type=MediaType.MOVIE,
        title="Interstellar",
        file_path="/movies/Interstellar/Interstellar.mkv",
        import_date=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
    )
    assert item_default.tags == []

    item_tagged = MediaInventoryItem(
        id="radarr:102",
        instance_name="radarr-main",
        instance_type=InstanceType.RADARR,
        media_type=MediaType.MOVIE,
        title="Dune",
        file_path="/movies/Dune/Dune.mkv",
        import_date=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
        tags=["4k", "favorite"],
    )
    assert item_tagged.tags == ["4k", "favorite"]
    parsed = json.loads(item_tagged.model_dump_json())
    assert parsed["tags"] == ["4k", "favorite"]


def test_media_inventory_item_optional_grab_date_none():
    """Verify grab_date=None validator does not fail."""
    item = MediaInventoryItem(
        id="radarr:102",
        instance_name="radarr-main",
        instance_type=InstanceType.RADARR,
        media_type=MediaType.MOVIE,
        title="Dune",
        file_path="/movies/Dune/Dune.mkv",
        import_date=datetime(2024, 2, 1, 0, 0, 0, tzinfo=UTC),
        grab_date=None,
    )
    assert item.grab_date is None


def test_media_inventory_item_multi_episode():
    """Verify multi-episode TV item representation."""
    item = MediaInventoryItem(
        id="sonarr:201",
        instance_name="sonarr-tv",
        instance_type=InstanceType.SONARR,
        media_type=MediaType.EPISODE,
        title="Breaking Bad",
        year=2008,
        season_number=1,
        episode_numbers=[1, 2],
        formatted_episode="S01E01-E02",
        episode_title="Pilot / Cat's in the Bag",
        series_id=10,
        episode_file_id=201,
        episode_ids=[301, 302],
        file_path="/tv/Breaking Bad/Breaking Bad - S01E01-E02.mkv",
        relative_path="Breaking Bad - S01E01-E02.mkv",
        size_bytes=3000000000,
        audio_languages=["English"],
        import_date=datetime(2024, 2, 1, 12, 0, 0, tzinfo=UTC),
        grab_date=datetime(2024, 2, 1, 10, 0, 0, tzinfo=UTC),
        age_days=50,
        history_status=HistoryStatus.GRABBED_AND_IMPORTED,
    )
    assert item.media_type == MediaType.EPISODE
    assert item.season_number == 1
    assert item.episode_numbers == [1, 2]
    assert item.formatted_episode == "S01E01-E02"
    assert item.episode_ids == [301, 302]
    assert item.history_status == HistoryStatus.GRABBED_AND_IMPORTED


def test_media_inventory_item_legacy_representation():
    """Verify legacy item representation when History API records are missing."""
    item = MediaInventoryItem(
        id="radarr:505",
        instance_name="radarr-main",
        instance_type=InstanceType.RADARR,
        media_type=MediaType.MOVIE,
        title="Classic Film",
        year=1980,
        movie_id=5,
        movie_file_id=505,
        file_path="/movies/Classic Film (1980)/Classic Film (1980).mkv",
        size_bytes=4000000000,
        import_date=datetime(2020, 5, 10, 15, 0, 0, tzinfo=UTC),
        grab_date=None,
        age_days=1500,
        has_history=False,
        is_legacy=True,
        history_status=HistoryStatus.LEGACY,
    )
    assert item.is_legacy is True
    assert item.has_history is False
    assert item.history_status == HistoryStatus.LEGACY
    assert item.grab_date is None


def test_media_inventory_item_serialization():
    """Verify serialization to dict and JSON roundtrip."""
    dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
    item = MediaInventoryItem(
        id="radarr:101",
        instance_name="radarr-main",
        instance_type=InstanceType.RADARR,
        media_type=MediaType.MOVIE,
        title="Interstellar",
        year=2014,
        file_path="/movies/Interstellar (2014)/Interstellar (2014).mkv",
        size_bytes=15000000000,
        audio_languages=["English"],
        import_date=dt,
    )
    d = item.model_dump()
    assert d["id"] == "radarr:101"
    assert d["instance_type"] == InstanceType.RADARR
    assert d["media_type"] == MediaType.MOVIE
    assert d["import_date"] == dt

    json_str = item.model_dump_json()
    parsed = json.loads(json_str)
    assert parsed["id"] == "radarr:101"
    assert parsed["title"] == "Interstellar"
    assert parsed["instance_type"] == "radarr"
    assert parsed["media_type"] == "movie"
    assert parsed["monitored"] is True


def test_media_inventory_item_monitored_field():
    """Verify MediaInventoryItem default monitored=True and explicit False/True handling."""
    dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
    item_default = MediaInventoryItem(
        id="radarr:101",
        instance_name="radarr-main",
        instance_type=InstanceType.RADARR,
        media_type=MediaType.MOVIE,
        title="Interstellar",
        file_path="/movies/Interstellar/Interstellar.mkv",
        import_date=dt,
    )
    assert item_default.monitored is True

    item_unmonitored = MediaInventoryItem(
        id="radarr:102",
        instance_name="radarr-main",
        instance_type=InstanceType.RADARR,
        media_type=MediaType.MOVIE,
        title="Dune",
        file_path="/movies/Dune/Dune.mkv",
        import_date=dt,
        monitored=False,
    )
    assert item_unmonitored.monitored is False
    parsed_unmonitored = json.loads(item_unmonitored.model_dump_json())
    assert parsed_unmonitored["monitored"] is False


def test_inventory_filter_defaults():
    """Verify InventoryFilter default field values."""
    f = InventoryFilter()
    assert f.media_types is None
    assert f.instance_names is None
    assert f.audio_langs is None
    assert f.min_size_bytes is None
    assert f.max_size_bytes is None
    assert f.min_age_days is None
    assert f.max_age_days is None
    assert f.before_date is None
    assert f.after_date is None
    assert f.legacy_only is False
    assert f.history_only is False
    assert f.monitored_only is False
    assert f.unmonitored_only is False


def test_inventory_summary_defaults():
    """Verify InventorySummary default field values."""
    s = InventorySummary()
    assert s.total_items == 0
    assert s.total_size_bytes == 0
    assert s.movie_count == 0
    assert s.episode_count == 0
    assert s.legacy_count == 0
    assert s.oldest_import_date is None
    assert s.newest_import_date is None
    assert s.oldest_grab_date is None
    assert s.instances_breakdown == {}


def test_enums_values():
    """Verify enum representations."""
    assert MediaType.MOVIE == "movie"
    assert MediaType.EPISODE == "episode"
    assert HistoryStatus.IMPORTED == "imported"
    assert HistoryStatus.GRABBED_AND_IMPORTED == "grabbed_and_imported"
    assert HistoryStatus.LEGACY == "legacy"
    assert HistoryStatus.UNINDEXED == "unindexed"
    assert SortKey.IMPORT_DATE == "import_date"
    assert SortKey.GRAB_DATE == "grab_date"
    assert SortKey.SIZE == "size"
    assert SortKey.TITLE == "title"
    assert SortKey.AGE == "age"
    assert SortDirection.ASC == "asc"
    assert SortDirection.DESC == "desc"


def test_package_reexports():
    """Verify symbols exported from package root."""
    assert LanguageNormalizer is not None
    assert LanguageEntry is not None
    assert parse_size is not None
    assert parse_age_cutoff is not None
    assert parse_date_cutoff is not None
    assert MediaInventoryItem is not None
    assert InventoryFilter is not None
    assert InventorySummary is not None
