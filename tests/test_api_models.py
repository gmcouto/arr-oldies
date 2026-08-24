"""Unit tests for Radarr and Sonarr Pydantic v2 API data models."""

from datetime import UTC, datetime

from arr_oldies.api.models import (
    MediaInfo,
    RadarrHistoryPage,
    RadarrMovie,
    SonarrEpisode,
    SonarrEpisodeFile,
    SonarrHistoryPage,
    SonarrSeries,
)


def test_media_info_parsing():
    """Verify MediaInfo deserialization and alias mapping."""
    payload = {
        "audioCodec": "EAC3",
        "audioChannels": 5.1,
        "audioProfile": "Atmos",
        "audioLanguages": "eng/fre",
        "audioTitle": "English",
        "videoCodec": "x265",
        "videoBitdepth": 10,
        "videoBitrate": 4500000,
        "videoFps": 23.976,
        "resolution": "1920x1080",
        "runTime": "01:45:30",
        "scanType": "Progressive",
        "subtitles": "eng/spa",
        "unknownExtraField": "ignored_value",
    }
    info = MediaInfo.model_validate(payload)
    assert info.audio_codec == "EAC3"
    assert info.audio_channels == 5.1
    assert info.audio_profile == "Atmos"
    assert info.audio_languages == "eng/fre"
    assert info.audio_title == "English"
    assert info.video_codec == "x265"
    assert info.video_bitdepth == 10
    assert info.video_bitrate == 4500000
    assert info.video_fps == 23.976
    assert info.resolution == "1920x1080"
    assert info.run_time == "01:45:30"
    assert info.scan_type == "Progressive"
    assert info.subtitles == "eng/spa"


def test_radarr_movie_and_file_parsing():
    """Verify RadarrMovie and RadarrMovieFile parsing with nested MediaInfo."""
    payload = {
        "id": 42,
        "title": "Inception",
        "year": 2010,
        "path": "/movies/Inception (2010)",
        "monitored": True,
        "hasFile": True,
        "movieFileId": 101,
        "sizeOnDisk": 15000000000,
        "genres": ["Action", "Sci-Fi"],
        "extraFutureField": "should be ignored",
        "movieFile": {
            "id": 101,
            "movieId": 42,
            "relativePath": "Inception (2010).mkv",
            "path": "/movies/Inception (2010)/Inception (2010).mkv",
            "size": 15000000000,
            "dateAdded": "2024-01-15T14:30:00Z",
            "indexerFlags": 0,
            "mediaInfo": {
                "audioCodec": "DTS-HD MA",
                "audioChannels": 7.1,
                "audioLanguages": "eng",
                "videoCodec": "x265",
            },
        },
    }
    movie = RadarrMovie.model_validate(payload)
    assert movie.id == 42
    assert movie.title == "Inception"
    assert movie.year == 2010
    assert movie.has_file is True
    assert movie.movie_file_id == 101
    assert movie.size_on_disk == 15000000000
    assert movie.genres == ["Action", "Sci-Fi"]
    assert movie.movie_file is not None
    assert movie.movie_file.id == 101
    assert movie.movie_file.movie_id == 42
    assert movie.movie_file.relative_path == "Inception (2010).mkv"
    assert movie.movie_file.date_added == datetime(2024, 1, 15, 14, 30, 0, tzinfo=UTC)
    assert movie.movie_file.media_info is not None
    assert movie.movie_file.media_info.audio_codec == "DTS-HD MA"
    assert movie.movie_file.media_info.audio_channels == 7.1


def test_radarr_history_parsing():
    """Verify Radarr history page and records parsing."""
    payload = {
        "page": 1,
        "pageSize": 1000,
        "totalRecords": 1,
        "records": [
            {
                "id": 501,
                "movieId": 42,
                "sourceTitle": "Inception.2010.1080p.BluRay.x264",
                "eventType": "downloadFolderImported",
                "date": "2024-01-15T14:35:00Z",
                "downloadId": "torrent_12345",
                "data": {
                    "fileId": "101",
                    "importedPath": "/movies/Inception (2010)/Inception (2010).mkv",
                },
            }
        ],
    }
    history_page = RadarrHistoryPage.model_validate(payload)
    assert history_page.page == 1
    assert history_page.page_size == 1000
    assert history_page.total_records == 1
    assert len(history_page.records) == 1

    rec = history_page.records[0]
    assert rec.id == 501
    assert rec.movie_id == 42
    assert rec.source_title == "Inception.2010.1080p.BluRay.x264"
    assert rec.event_type == "downloadFolderImported"
    assert rec.date == datetime(2024, 1, 15, 14, 35, 0, tzinfo=UTC)
    assert rec.download_id == "torrent_12345"
    assert rec.data["fileId"] == "101"


def test_sonarr_series_and_episodes_parsing():
    """Verify SonarrSeries, SonarrEpisodeFile, and SonarrEpisode parsing."""
    series_payload = {
        "id": 10,
        "title": "Breaking Bad",
        "year": 2008,
        "path": "/tv/Breaking Bad",
        "monitored": True,
        "seasons": [
            {
                "seasonNumber": 1,
                "monitored": True,
                "statistics": {"episodeFileCount": 7, "totalEpisodeCount": 7},
            }
        ],
    }
    series = SonarrSeries.model_validate(series_payload)
    assert series.id == 10
    assert series.title == "Breaking Bad"
    assert len(series.seasons) == 1
    assert series.seasons[0].season_number == 1
    assert series.seasons[0].monitored is True

    episode_file_payload = {
        "id": 201,
        "seriesId": 10,
        "seasonNumber": 1,
        "relativePath": "Season 01/Breaking Bad - S01E01.mkv",
        "path": "/tv/Breaking Bad/Season 01/Breaking Bad - S01E01.mkv",
        "size": 2500000000,
        "dateAdded": "2024-02-01T10:00:00Z",
        "mediaInfo": {
            "audioCodec": "AC3",
            "audioChannels": 5.1,
            "audioLanguages": "eng/spa",
        },
    }
    ep_file = SonarrEpisodeFile.model_validate(episode_file_payload)
    assert ep_file.id == 201
    assert ep_file.series_id == 10
    assert ep_file.season_number == 1
    assert ep_file.date_added == datetime(2024, 2, 1, 10, 0, 0, tzinfo=UTC)
    assert ep_file.media_info is not None
    assert ep_file.media_info.audio_languages == "eng/spa"

    episode_payload = {
        "id": 301,
        "seriesId": 10,
        "episodeFileId": 201,
        "seasonNumber": 1,
        "episodeNumber": 1,
        "title": "Pilot",
        "airDateUtc": "2008-01-20T00:00:00Z",
        "monitored": True,
        "hasFile": True,
    }
    episode = SonarrEpisode.model_validate(episode_payload)
    assert episode.id == 301
    assert episode.series_id == 10
    assert episode.episode_file_id == 201
    assert episode.season_number == 1
    assert episode.episode_number == 1
    assert episode.title == "Pilot"
    assert episode.air_date_utc == datetime(2008, 1, 20, 0, 0, 0, tzinfo=UTC)
    assert episode.has_file is True


def test_sonarr_history_parsing():
    """Verify Sonarr history page and records parsing."""
    payload = {
        "page": 1,
        "pageSize": 1000,
        "totalRecords": 1,
        "records": [
            {
                "id": 9001,
                "seriesId": 10,
                "episodeId": 301,
                "sourceTitle": "Breaking.Bad.S01E01.1080p.BluRay.x264",
                "eventType": "downloadFolderImported",
                "date": "2024-02-01T10:05:00Z",
                "data": {
                    "fileId": "201",
                    "importedPath": "/tv/Breaking Bad/Season 01/Breaking Bad - S01E01.mkv",
                },
            }
        ],
    }
    history_page = SonarrHistoryPage.model_validate(payload)
    assert history_page.page == 1
    assert history_page.total_records == 1
    assert len(history_page.records) == 1
    rec = history_page.records[0]
    assert rec.id == 9001
    assert rec.series_id == 10
    assert rec.episode_id == 301
    assert rec.event_type == "downloadFolderImported"
