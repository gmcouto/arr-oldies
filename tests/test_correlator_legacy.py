"""Unit tests for legacy media items fallback when History API records are missing (INVT-06)."""

from datetime import UTC, datetime

from arr_oldies.api.fetcher import InstanceMediaData
from arr_oldies.api.models import (
    RadarrMovie,
    RadarrMovieFile,
    SonarrEpisode,
    SonarrEpisodeFile,
    SonarrSeries,
)
from arr_oldies.inventory.correlator import HistoryCorrelator
from arr_oldies.inventory.models import HistoryStatus, MediaType
from arr_oldies.models import InstanceType


def test_correlate_legacy_radarr_file_without_history():
    """Verify Radarr files with no history events fall back to date_added and are tagged as legacy."""
    movie = RadarrMovie(id=5, title="Classic Film", year=1980, path="/movies/Classic Film (1980)")
    movie_file = RadarrMovieFile(
        id=505,
        movie_id=5,
        relative_path="Classic Film (1980).mkv",
        path="/movies/Classic Film (1980)/Classic Film (1980).mkv",
        size=4000000000,
        date_added=datetime(2020, 5, 10, 15, 0, 0, tzinfo=UTC),
    )
    data = InstanceMediaData(
        instance_name="radarr-legacy",
        instance_type=InstanceType.RADARR,
        movies=[movie],
        movie_files=[movie_file],
        history_records=[],  # Empty history
    )

    correlator = HistoryCorrelator()
    ref_time = datetime(2020, 5, 20, 15, 0, 0, tzinfo=UTC)
    items = correlator.correlate_instance(data, reference_time=ref_time)

    assert len(items) == 1
    item = items[0]
    assert item.id == "radarr-legacy:505"
    assert item.media_type == MediaType.MOVIE
    assert item.is_legacy is True
    assert item.has_history is False
    assert item.history_status == HistoryStatus.LEGACY
    assert item.import_date == datetime(2020, 5, 10, 15, 0, 0, tzinfo=UTC)
    assert item.grab_date is None
    assert item.age_days == 10
    assert item.source_title is None
    assert item.download_id is None


def test_correlate_legacy_sonarr_file_without_history():
    """Verify Sonarr files with no history events fall back to date_added and are tagged as legacy."""
    series = SonarrSeries(id=50, title="Old Classic Series", year=1995, path="/tv/Old Classic Series")
    ep_file = SonarrEpisodeFile(
        id=801,
        series_id=50,
        season_number=1,
        relative_path="Old.Classic.S01E01.mkv",
        path="/tv/Old Classic Series/Season 01/Old.Classic.S01E01.mkv",
        size=1200000000,
        date_added=datetime(2019, 1, 1, 0, 0, 0, tzinfo=UTC),
    )
    episodes = [
        SonarrEpisode(
            id=1201,
            series_id=50,
            episode_file_id=801,
            season_number=1,
            episode_number=1,
            title="Premiere",
        )
    ]
    data = InstanceMediaData(
        instance_name="sonarr-legacy",
        instance_type=InstanceType.SONARR,
        series=[series],
        episode_files=[ep_file],
        episodes=episodes,
        history_records=[],  # Empty / pruned history
    )

    correlator = HistoryCorrelator()
    ref_time = datetime(2019, 1, 31, 0, 0, 0, tzinfo=UTC)
    items = correlator.correlate_instance(data, reference_time=ref_time)

    assert len(items) == 1
    item = items[0]
    assert item.id == "sonarr-legacy:801"
    assert item.media_type == MediaType.EPISODE
    assert item.is_legacy is True
    assert item.has_history is False
    assert item.history_status == HistoryStatus.LEGACY
    assert item.import_date == datetime(2019, 1, 1, 0, 0, 0, tzinfo=UTC)
    assert item.grab_date is None
    assert item.age_days == 30
    assert item.formatted_episode == "S01E01"
    assert item.episode_title == "Premiere"
