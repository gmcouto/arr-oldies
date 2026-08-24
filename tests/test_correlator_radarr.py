"""Unit tests for HistoryCorrelator with Radarr movie files and history events."""

from datetime import UTC, datetime

import pytest

from arr_oldies.api.fetcher import InstanceMediaData
from arr_oldies.api.models import (
    MediaInfo,
    RadarrHistoryRecord,
    RadarrMovie,
    RadarrMovieFile,
    Tag,
)
from arr_oldies.inventory.correlator import HistoryCorrelator
from arr_oldies.inventory.models import HistoryStatus, MediaType
from arr_oldies.models import InstanceType


def test_correlate_radarr_movie_tag_label_mapping():
    """Verify movie numeric tag IDs resolve to human-readable tag labels."""
    movie_tagged = RadarrMovie(
        id=1,
        title="Inception",
        year=2010,
        path="/movies/Inception (2010)",
        tags=[10, 20, 99],  # 99 is unmapped/missing
    )
    movie_untagged = RadarrMovie(
        id=2,
        title="Dune",
        year=2021,
        path="/movies/Dune (2021)",
        tags=[],
    )
    file1 = RadarrMovieFile(
        id=101,
        movie_id=1,
        relative_path="Inception.mkv",
        path="/movies/Inception (2010)/Inception.mkv",
        size=1000000000,
        date_added=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
    )
    file2 = RadarrMovieFile(
        id=102,
        movie_id=2,
        relative_path="Dune.mkv",
        path="/movies/Dune (2021)/Dune.mkv",
        size=2000000000,
        date_added=datetime(2024, 1, 2, 0, 0, 0, tzinfo=UTC),
    )
    data = InstanceMediaData(
        instance_name="radarr-main",
        instance_type=InstanceType.RADARR,
        movies=[movie_tagged, movie_untagged],
        movie_files=[file1, file2],
        tags=[
            Tag(id=10, label="4k"),
            Tag(id=20, label="favorite"),
            Tag(id=30, label="archive"),
        ],
        history_records=[],
    )

    correlator = HistoryCorrelator()
    items = correlator.correlate_instance(data)

    assert len(items) == 2
    items_by_id = {item.movie_file_id: item for item in items}
    assert items_by_id[101].tags == ["4k", "favorite"]
    assert items_by_id[102].tags == []


def test_correlate_radarr_movie_exact_file_id_and_download_id_match():
    """Verify correlation matches downloadFolderImported event by fileId and grabbed by downloadId."""
    movie = RadarrMovie(id=1, title="Inception", year=2010, path="/movies/Inception (2010)")
    movie_file = RadarrMovieFile(
        id=101,
        movie_id=1,
        relative_path="Inception (2010).mkv",
        path="/movies/Inception (2010)/Inception (2010).mkv",
        size=10000000000,
        date_added=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
        media_info=MediaInfo(audio_languages="eng/fre", video_codec="x265", resolution="1080p"),
    )
    history = [
        RadarrHistoryRecord(
            id=501,
            movie_id=1,
            source_title="Inception.2010.BluRay",
            event_type="downloadFolderImported",
            date=datetime(2024, 1, 1, 10, 0, 0, tzinfo=UTC),
            download_id="dl_123",
            data={"fileId": "101", "importedPath": "/movies/Inception (2010)/Inception (2010).mkv"},
        ),
        RadarrHistoryRecord(
            id=500,
            movie_id=1,
            source_title="Inception.2010.BluRay.Release",
            event_type="grabbed",
            date=datetime(2024, 1, 1, 8, 0, 0, tzinfo=UTC),
            download_id="dl_123",
        ),
    ]
    data = InstanceMediaData(
        instance_name="radarr-main",
        instance_type=InstanceType.RADARR,
        movies=[movie],
        movie_files=[movie_file],
        history_records=history,
    )

    correlator = HistoryCorrelator()
    ref_time = datetime(2024, 1, 11, 10, 0, 0, tzinfo=UTC)
    items = correlator.correlate_instance(data, reference_time=ref_time)

    assert len(items) == 1
    item = items[0]
    assert item.id == "radarr-main:101"
    assert item.instance_name == "radarr-main"
    assert item.instance_type == InstanceType.RADARR
    assert item.title == "Inception"
    assert item.year == 2010
    assert item.media_type == MediaType.MOVIE
    assert item.import_date == datetime(2024, 1, 1, 10, 0, 0, tzinfo=UTC)
    assert item.grab_date == datetime(2024, 1, 1, 8, 0, 0, tzinfo=UTC)
    assert item.age_days == 10
    assert item.audio_languages == ["English", "French"]
    assert item.video_codec == "x265"
    assert item.resolution == "1080p"
    assert item.history_status == HistoryStatus.GRABBED_AND_IMPORTED
    assert item.has_history is True
    assert item.is_legacy is False
    assert item.download_id == "dl_123"
    assert item.source_title == "Inception.2010.BluRay"


def test_correlate_radarr_path_matching_fallback():
    """Verify fallback to matching by importedPath when fileId is absent in history event data."""
    movie = RadarrMovie(id=2, title="Interstellar", year=2014, path="/movies/Interstellar")
    movie_file = RadarrMovieFile(
        id=202,
        movie_id=2,
        relative_path="Interstellar.mkv",
        path="/movies/Interstellar/Interstellar.mkv",
        size=15000000000,
        date_added=datetime(2024, 2, 1, 0, 0, 0, tzinfo=UTC),
        media_info=MediaInfo(audio_languages="Japanese, English"),
    )
    history = [
        RadarrHistoryRecord(
            id=601,
            movie_id=2,
            source_title="Interstellar.2014.Remux",
            event_type="movieFileImported",
            date=datetime(2024, 2, 1, 15, 0, 0, tzinfo=UTC),
            data={"importedPath": "/movies/Interstellar/Interstellar.mkv"},  # No fileId
        ),
    ]
    data = InstanceMediaData(
        instance_name="radarr-4k",
        instance_type=InstanceType.RADARR,
        movies=[movie],
        movie_files=[movie_file],
        history_records=history,
    )

    correlator = HistoryCorrelator()
    ref_time = datetime(2024, 2, 11, 15, 0, 0, tzinfo=UTC)
    items = correlator.correlate_instance(data, reference_time=ref_time)

    assert len(items) == 1
    item = items[0]
    assert item.title == "Interstellar"
    assert item.import_date == datetime(2024, 2, 1, 15, 0, 0, tzinfo=UTC)
    assert item.grab_date is None
    assert item.history_status == HistoryStatus.IMPORTED
    assert item.has_history is True
    assert item.is_legacy is False
    assert item.audio_languages == ["Japanese", "English"]


def test_correlate_radarr_upgraded_file_precedence():
    """Verify that when multiple import events exist for the same file/movie, newest import event is chosen."""
    movie = RadarrMovie(id=3, title="Dune", year=2021, path="/movies/Dune")
    movie_file = RadarrMovieFile(
        id=303,
        movie_id=3,
        relative_path="Dune.mkv",
        path="/movies/Dune/Dune.mkv",
        size=20000000000,
        date_added=datetime(2024, 3, 15, 0, 0, 0, tzinfo=UTC),
        media_info=MediaInfo(audio_languages="eng"),
    )
    history = [
        # Older 720p version
        RadarrHistoryRecord(
            id=700,
            movie_id=3,
            source_title="Dune.2021.720p",
            event_type="downloadFolderImported",
            date=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
            download_id="dl_old",
            data={"fileId": "303"},
        ),
        # Newer 4K upgrade
        RadarrHistoryRecord(
            id=701,
            movie_id=3,
            source_title="Dune.2021.2160p.UHD",
            event_type="downloadFolderImported",
            date=datetime(2024, 3, 15, 12, 0, 0, tzinfo=UTC),
            download_id="dl_new",
            data={"fileId": "303"},
        ),
        RadarrHistoryRecord(
            id=702,
            movie_id=3,
            source_title="Dune.2021.2160p.UHD",
            event_type="grabbed",
            date=datetime(2024, 3, 15, 10, 0, 0, tzinfo=UTC),
            download_id="dl_new",
        ),
    ]
    data = InstanceMediaData(
        instance_name="radarr-main",
        instance_type=InstanceType.RADARR,
        movies=[movie],
        movie_files=[movie_file],
        history_records=history,
    )

    correlator = HistoryCorrelator()
    items = correlator.correlate_instance(data)

    assert len(items) == 1
    item = items[0]
    assert item.import_date == datetime(2024, 3, 15, 12, 0, 0, tzinfo=UTC)
    assert item.grab_date == datetime(2024, 3, 15, 10, 0, 0, tzinfo=UTC)
    assert item.download_id == "dl_new"
    assert item.source_title == "Dune.2021.2160p.UHD"


def test_correlate_radarr_unsupported_instance_type():
    """Verify ValueError is raised if instance_type is invalid."""
    data = InstanceMediaData.model_construct(
        instance_name="bad-inst",
        instance_type="other",  # type: ignore[arg-type]
    )
    correlator = HistoryCorrelator()
    with pytest.raises(ValueError, match="Unsupported instance type"):
        correlator.correlate_instance(data)


def test_correlate_radarr_monitored_status():
    """Verify Radarr movie monitored status is propagated to MediaInventoryItem."""
    movie_monitored = RadarrMovie(
        id=1, title="Monitored Movie", year=2020, path="/movies/M1", monitored=True
    )
    file_monitored = RadarrMovieFile(
        id=101,
        movie_id=1,
        relative_path="M1.mkv",
        path="/movies/M1/M1.mkv",
        size=1000000,
        date_added=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
    )
    movie_unmonitored = RadarrMovie(
        id=2, title="Unmonitored Movie", year=2021, path="/movies/M2", monitored=False
    )
    file_unmonitored = RadarrMovieFile(
        id=102,
        movie_id=2,
        relative_path="M2.mkv",
        path="/movies/M2/M2.mkv",
        size=1000000,
        date_added=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
    )
    data = InstanceMediaData(
        instance_name="radarr-main",
        instance_type=InstanceType.RADARR,
        movies=[movie_monitored, movie_unmonitored],
        movie_files=[file_monitored, file_unmonitored],
        history_records=[],
    )

    correlator = HistoryCorrelator()
    items = correlator.correlate_instance(data)

    assert len(items) == 2
    items_by_id = {item.movie_file_id: item for item in items}
    assert items_by_id[101].monitored is True
    assert items_by_id[102].monitored is False


def test_correlate_radarr_missing_movie_monitored_fallback():
    """Verify Radarr fallback to monitored=True when movie object is missing."""
    file_orphan = RadarrMovieFile(
        id=103,
        movie_id=999,
        relative_path="Orphan.mkv",
        path="/movies/Orphan/Orphan.mkv",
        size=1000000,
        date_added=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
    )
    data = InstanceMediaData(
        instance_name="radarr-main",
        instance_type=InstanceType.RADARR,
        movies=[],
        movie_files=[file_orphan],
        history_records=[],
    )

    correlator = HistoryCorrelator()
    items = correlator.correlate_instance(data)

    assert len(items) == 1
    assert items[0].monitored is True
