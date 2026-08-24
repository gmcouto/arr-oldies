"""Unit tests for HistoryCorrelator with Sonarr TV series and multi-episode files."""

from datetime import UTC, datetime

from arr_oldies.api.fetcher import InstanceMediaData
from arr_oldies.api.models import (
    MediaInfo,
    SonarrEpisode,
    SonarrEpisodeFile,
    SonarrHistoryRecord,
    SonarrSeries,
)
from arr_oldies.inventory.correlator import HistoryCorrelator
from arr_oldies.inventory.models import HistoryStatus, MediaType
from arr_oldies.models import InstanceType


def test_correlate_sonarr_single_episode():
    """Verify Sonarr single episode file correlation and badge formatting."""
    series = SonarrSeries(id=10, title="Breaking Bad", year=2008, path="/tv/Breaking Bad")
    ep_file = SonarrEpisodeFile(
        id=201,
        series_id=10,
        season_number=1,
        relative_path="Breaking Bad - S01E01.mkv",
        path="/tv/Breaking Bad/Season 01/Breaking Bad - S01E01.mkv",
        size=2500000000,
        date_added=datetime(2024, 2, 1, 0, 0, 0, tzinfo=UTC),
        media_info=MediaInfo(audio_languages="eng", video_codec="x264", resolution="1080p"),
    )
    episodes = [
        SonarrEpisode(
            id=301,
            series_id=10,
            episode_file_id=201,
            season_number=1,
            episode_number=1,
            title="Pilot",
        ),
    ]
    history = [
        SonarrHistoryRecord(
            id=9001,
            series_id=10,
            episode_id=301,
            source_title="Breaking.Bad.S01E01.1080p",
            event_type="downloadFolderImported",
            date=datetime(2024, 2, 1, 12, 0, 0, tzinfo=UTC),
            download_id="dl_bb1",
            data={"fileId": "201"},
        ),
        SonarrHistoryRecord(
            id=9000,
            series_id=10,
            episode_id=301,
            source_title="Breaking.Bad.S01E01.1080p",
            event_type="grabbed",
            date=datetime(2024, 2, 1, 11, 0, 0, tzinfo=UTC),
            download_id="dl_bb1",
        ),
    ]
    data = InstanceMediaData(
        instance_name="sonarr-tv",
        instance_type=InstanceType.SONARR,
        series=[series],
        episode_files=[ep_file],
        episodes=episodes,
        history_records=history,
    )

    correlator = HistoryCorrelator()
    ref_time = datetime(2024, 2, 11, 12, 0, 0, tzinfo=UTC)
    items = correlator.correlate_instance(data, reference_time=ref_time)

    assert len(items) == 1
    item = items[0]
    assert item.id == "sonarr-tv:201"
    assert item.media_type == MediaType.EPISODE
    assert item.title == "Breaking Bad"
    assert item.season_number == 1
    assert item.episode_numbers == [1]
    assert item.formatted_episode == "S01E01"
    assert item.episode_title == "Pilot"
    assert item.series_id == 10
    assert item.episode_file_id == 201
    assert item.episode_ids == [301]
    assert item.import_date == datetime(2024, 2, 1, 12, 0, 0, tzinfo=UTC)
    assert item.grab_date == datetime(2024, 2, 1, 11, 0, 0, tzinfo=UTC)
    assert item.age_days == 10
    assert item.audio_languages == ["English"]
    assert item.history_status == HistoryStatus.GRABBED_AND_IMPORTED
    assert item.has_history is True
    assert item.is_legacy is False


def test_correlate_sonarr_multi_episode_file():
    """Verify Sonarr multi-episode files format formatted_episode as 'S01E01-E02'."""
    series = SonarrSeries(id=10, title="Breaking Bad", year=2008, path="/tv/Breaking Bad")
    ep_file = SonarrEpisodeFile(
        id=202,
        series_id=10,
        season_number=1,
        relative_path="Breaking Bad - S01E01-E02.mkv",
        path="/tv/Breaking Bad/Season 01/Breaking Bad - S01E01-E02.mkv",
        size=4500000000,
        date_added=datetime(2024, 2, 1, 0, 0, 0, tzinfo=UTC),
        media_info=MediaInfo(audio_languages="Japanese, English"),
    )
    episodes = [
        SonarrEpisode(
            id=301,
            series_id=10,
            episode_file_id=202,
            season_number=1,
            episode_number=1,
            title="Pilot",
        ),
        SonarrEpisode(
            id=302,
            series_id=10,
            episode_file_id=202,
            season_number=1,
            episode_number=2,
            title="Cat's in the Bag",
        ),
    ]
    history = [
        SonarrHistoryRecord(
            id=9002,
            series_id=10,
            episode_id=301,
            source_title="Breaking.Bad.S01E01E02",
            event_type="downloadFolderImported",
            date=datetime(2024, 2, 1, 12, 0, 0, tzinfo=UTC),
            data={"fileId": "202"},
        )
    ]
    data = InstanceMediaData(
        instance_name="sonarr-tv",
        instance_type=InstanceType.SONARR,
        series=[series],
        episode_files=[ep_file],
        episodes=episodes,
        history_records=history,
    )

    correlator = HistoryCorrelator()
    items = correlator.correlate_instance(data)

    assert len(items) == 1
    item = items[0]
    assert item.media_type == MediaType.EPISODE
    assert item.title == "Breaking Bad"
    assert item.formatted_episode == "S01E01-E02"
    assert item.episode_numbers == [1, 2]
    assert item.episode_ids == [301, 302]
    assert item.episode_title is None  # Multiple episodes -> no single title
    assert item.audio_languages == ["Japanese", "English"]


def test_correlate_sonarr_without_episodes_list():
    """Verify fallback formatting 'S02' when episodes metadata is empty."""
    series = SonarrSeries(id=20, title="Better Call Saul", year=2015, path="/tv/BCS")
    ep_file = SonarrEpisodeFile(
        id=401,
        series_id=20,
        season_number=2,
        relative_path="BCS - S02.mkv",
        path="/tv/BCS/BCS - S02.mkv",
        size=1000000000,
        date_added=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
    )
    data = InstanceMediaData(
        instance_name="sonarr-tv",
        instance_type=InstanceType.SONARR,
        series=[series],
        episode_files=[ep_file],
        episodes=[],
        history_records=[],
    )

    correlator = HistoryCorrelator()
    items = correlator.correlate_instance(data)

    assert len(items) == 1
    assert items[0].formatted_episode == "S02"
    assert items[0].is_legacy is True
