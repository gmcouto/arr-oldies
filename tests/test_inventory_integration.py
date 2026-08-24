"""End-to-end integration tests verifying the full multi-instance inventory pipeline."""

from datetime import UTC, datetime

from arr_oldies.api.fetcher import InstanceMediaData
from arr_oldies.api.models import (
    MediaInfo,
    RadarrHistoryRecord,
    RadarrMovie,
    RadarrMovieFile,
    SonarrEpisode,
    SonarrEpisodeFile,
    SonarrHistoryRecord,
    SonarrSeries,
)
from arr_oldies.inventory import (
    HistoryCorrelator,
    InventoryEngine,
    InventoryFilter,
    MediaType,
    SortDirection,
    SortKey,
    parse_age_cutoff,
    parse_size,
)
from arr_oldies.models import InstanceType


def test_multi_instance_inventory_pipeline_end_to_end():
    """Verify end-to-end multi-instance correlation, parsing, filtering, sorting, and metrics generation."""
    ref_time = datetime(2024, 6, 1, 0, 0, 0, tzinfo=UTC)

    # 1. Instance: radarr-4k (4K movie library with full history)
    radarr_4k_data = InstanceMediaData(
        instance_name="radarr-4k",
        instance_type=InstanceType.RADARR,
        movies=[
            RadarrMovie(id=1, title="Oppenheimer", year=2023, path="/movies/Oppenheimer (2023)"),
            RadarrMovie(id=2, title="Dune: Part Two", year=2024, path="/movies/Dune Part Two (2024)"),
        ],
        movie_files=[
            RadarrMovieFile(
                id=101,
                movie_id=1,
                relative_path="Oppenheimer.mkv",
                path="/movies/Oppenheimer (2023)/Oppenheimer.mkv",
                size=45_000_000_000,
                date_added=datetime(2023, 11, 20, 0, 0, 0, tzinfo=UTC),
                media_info=MediaInfo(audio_languages="eng/fre", video_codec="x265", resolution="2160p"),
            ),
            RadarrMovieFile(
                id=102,
                movie_id=2,
                relative_path="Dune.2.mkv",
                path="/movies/Dune Part Two (2024)/Dune.2.mkv",
                size=50_000_000_000,
                date_added=datetime(2024, 4, 15, 0, 0, 0, tzinfo=UTC),
                media_info=MediaInfo(audio_languages="eng", video_codec="x265", resolution="2160p"),
            ),
        ],
        history_records=[
            RadarrHistoryRecord(
                id=1001,
                movie_id=1,
                source_title="Oppenheimer.2023.2160p",
                event_type="downloadFolderImported",
                date=datetime(2023, 11, 20, 10, 0, 0, tzinfo=UTC),
                download_id="dl_opp",
                data={"fileId": "101"},
            ),
            RadarrHistoryRecord(
                id=1000,
                movie_id=1,
                source_title="Oppenheimer.2023.2160p",
                event_type="grabbed",
                date=datetime(2023, 11, 19, 8, 0, 0, tzinfo=UTC),
                download_id="dl_opp",
            ),
            RadarrHistoryRecord(
                id=1002,
                movie_id=2,
                source_title="Dune.Part.Two.2024.2160p",
                event_type="downloadFolderImported",
                date=datetime(2024, 4, 15, 14, 0, 0, tzinfo=UTC),
                download_id="dl_dune",
                data={"fileId": "102"},
            ),
        ],
    )

    # 2. Instance: radarr-hd (Legacy movie library with pruned/empty history)
    radarr_hd_data = InstanceMediaData(
        instance_name="radarr-hd",
        instance_type=InstanceType.RADARR,
        movies=[
            RadarrMovie(id=3, title="Casablanca", year=1942, path="/movies/Casablanca (1942)"),
            RadarrMovie(id=4, title="Seven Samurai", year=1954, path="/movies/Seven Samurai (1954)"),
        ],
        movie_files=[
            RadarrMovieFile(
                id=201,
                movie_id=3,
                relative_path="Casablanca.mkv",
                path="/movies/Casablanca (1942)/Casablanca.mkv",
                size=8_000_000_000,
                date_added=datetime(2018, 5, 10, 12, 0, 0, tzinfo=UTC),
                media_info=MediaInfo(audio_languages="eng"),
            ),
            RadarrMovieFile(
                id=202,
                movie_id=4,
                relative_path="Seven.Samurai.mkv",
                path="/movies/Seven Samurai (1954)/Seven.Samurai.mkv",
                size=12_000_000_000,
                date_added=datetime(2019, 1, 1, 0, 0, 0, tzinfo=UTC),
                media_info=MediaInfo(audio_languages="Japanese"),
            ),
        ],
        history_records=[],  # Legacy untracked files
    )

    # 3. Instance: sonarr-anime (Anime series with multi-episode file and dual audio)
    sonarr_anime_data = InstanceMediaData(
        instance_name="sonarr-anime",
        instance_type=InstanceType.SONARR,
        series=[
            SonarrSeries(id=10, title="Attack on Titan", year=2013, path="/anime/Attack on Titan"),
        ],
        episode_files=[
            SonarrEpisodeFile(
                id=301,
                series_id=10,
                season_number=1,
                relative_path="AOT.S01E01-E02.mkv",
                path="/anime/Attack on Titan/AOT.S01E01-E02.mkv",
                size=3_000_000_000,
                date_added=datetime(2023, 1, 10, 0, 0, 0, tzinfo=UTC),
                media_info=MediaInfo(audio_languages="Japanese, English", video_codec="x265", resolution="1080p"),
            ),
            SonarrEpisodeFile(
                id=302,
                series_id=10,
                season_number=1,
                relative_path="AOT.S01E03.mkv",
                path="/anime/Attack on Titan/AOT.S01E03.mkv",
                size=1_500_000_000,
                date_added=datetime(2023, 1, 15, 0, 0, 0, tzinfo=UTC),
                media_info=MediaInfo(audio_languages="Japanese, English"),
            ),
        ],
        episodes=[
            SonarrEpisode(id=1001, series_id=10, episode_file_id=301, season_number=1, episode_number=1, title="To You"),
            SonarrEpisode(id=1002, series_id=10, episode_file_id=301, season_number=1, episode_number=2, title="That Day"),
            SonarrEpisode(id=1003, series_id=10, episode_file_id=302, season_number=1, episode_number=3, title="A Dim Light"),
        ],
        history_records=[
            SonarrHistoryRecord(
                id=3001,
                series_id=10,
                episode_id=1001,
                source_title="AOT.S01E01E02.1080p",
                event_type="downloadFolderImported",
                date=datetime(2023, 1, 10, 12, 0, 0, tzinfo=UTC),
                download_id="dl_aot",
                data={"fileId": "301"},
            ),
            SonarrHistoryRecord(
                id=3000,
                series_id=10,
                episode_id=1001,
                source_title="AOT.S01E01E02.1080p",
                event_type="grabbed",
                date=datetime(2023, 1, 9, 20, 0, 0, tzinfo=UTC),
                download_id="dl_aot",
            ),
            SonarrHistoryRecord(
                id=3002,
                series_id=10,
                episode_id=1003,
                source_title="AOT.S01E03.1080p",
                event_type="downloadFolderImported",
                date=datetime(2023, 1, 15, 12, 0, 0, tzinfo=UTC),
                download_id="dl_aot3",
                data={"fileId": "302"},
            ),
        ],
    )

    # 4. Instance: sonarr-tv (Standard TV series)
    sonarr_tv_data = InstanceMediaData(
        instance_name="sonarr-tv",
        instance_type=InstanceType.SONARR,
        series=[
            SonarrSeries(id=20, title="Succession", year=2018, path="/tv/Succession"),
        ],
        episode_files=[
            SonarrEpisodeFile(
                id=401,
                series_id=20,
                season_number=1,
                relative_path="Succession.S01E01.mkv",
                path="/tv/Succession/Season 01/Succession.S01E01.mkv",
                size=4_000_000_000,
                date_added=datetime(2023, 5, 1, 0, 0, 0, tzinfo=UTC),
                media_info=MediaInfo(audio_languages="eng"),
            ),
            SonarrEpisodeFile(
                id=402,
                series_id=20,
                season_number=4,
                relative_path="Succession.S04E10.mkv",
                path="/tv/Succession/Season 04/Succession.S04E10.mkv",
                size=5_000_000_000,
                date_added=datetime(2024, 5, 29, 0, 0, 0, tzinfo=UTC),
                media_info=MediaInfo(audio_languages="eng"),
            ),
        ],
        episodes=[
            SonarrEpisode(id=2001, series_id=20, episode_file_id=401, season_number=1, episode_number=1, title="Celebration"),
            SonarrEpisode(id=2002, series_id=20, episode_file_id=402, season_number=4, episode_number=10, title="With Open Eyes"),
        ],
        history_records=[
            SonarrHistoryRecord(
                id=4001,
                series_id=20,
                episode_id=2001,
                source_title="Succession.S01E01",
                event_type="downloadFolderImported",
                date=datetime(2023, 5, 1, 10, 0, 0, tzinfo=UTC),
                data={"fileId": "401"},
            ),
            SonarrHistoryRecord(
                id=4002,
                series_id=20,
                episode_id=2002,
                source_title="Succession.S04E10",
                event_type="downloadFolderImported",
                date=datetime(2024, 5, 29, 10, 0, 0, tzinfo=UTC),
                data={"fileId": "402"},
            ),
        ],
    )

    # --- Pipeline Execution ---
    correlator = HistoryCorrelator()
    all_items = []
    for inst_data in [radarr_4k_data, radarr_hd_data, sonarr_anime_data, sonarr_tv_data]:
        items = correlator.correlate_instance(inst_data, reference_time=ref_time)
        all_items.extend(items)

    assert len(all_items) == 8

    # Validate inventory structure and legacy tracking
    movies = [i for i in all_items if i.media_type == MediaType.MOVIE]
    episodes = [i for i in all_items if i.media_type == MediaType.EPISODE]
    assert len(movies) == 4
    assert len(episodes) == 4

    legacy_items = [i for i in all_items if i.is_legacy]
    assert len(legacy_items) == 2
    assert {i.title for i in legacy_items} == {"Casablanca", "Seven Samurai"}

    # Multi-episode formatting check
    aot_multi = next(i for i in all_items if i.id == "sonarr-anime:301")
    assert aot_multi.formatted_episode == "S01E01-E02"
    assert aot_multi.audio_languages == ["Japanese", "English"]

    # Filter with parsed criteria: min size 2GB, min age 90 days, audio language "ja"
    min_size = parse_size("2GB")  # 2,000,000,000 bytes
    min_age = parse_age_cutoff("90d")  # 90 days
    criteria = InventoryFilter(
        min_size_bytes=min_size,
        min_age_days=min_age,
        audio_langs=["ja"],
    )

    engine = InventoryEngine()
    filtered = engine.filter_inventory(all_items, criteria)

    # Seven Samurai (12GB, >90d, Japanese) and AOT S01E01-E02 (3GB, >90d, Japanese)
    assert len(filtered) == 2
    assert {i.title for i in filtered} == {"Seven Samurai", "Attack on Titan"}

    # Filter further to only TV episodes
    ep_criteria = InventoryFilter(
        media_types=[MediaType.EPISODE],
        min_size_bytes=min_size,
        min_age_days=min_age,
        audio_langs=["ja"],
    )
    filtered_ep = engine.filter_inventory(all_items, ep_criteria)
    assert len(filtered_ep) == 1
    assert filtered_ep[0].title == "Attack on Titan"
    assert filtered_ep[0].formatted_episode == "S01E01-E02"

    # Sorting all items oldest-first by import date
    sorted_items = engine.sort_inventory(all_items, SortKey.IMPORT_DATE, SortDirection.ASC)
    assert [i.title for i in sorted_items] == [
        "Casablanca",
        "Seven Samurai",
        "Attack on Titan",
        "Attack on Titan",
        "Succession",
        "Oppenheimer",
        "Dune: Part Two",
        "Succession",
    ]

    # Generate summary metrics across entire unified inventory
    summary = engine.generate_summary(all_items)
    assert summary.total_items == 8
    assert summary.movie_count == 4
    assert summary.episode_count == 4
    assert summary.legacy_count == 2
    assert summary.total_size_bytes == 128_500_000_000
    assert summary.oldest_import_date == datetime(2018, 5, 10, 12, 0, 0, tzinfo=UTC)
    assert summary.newest_import_date == datetime(2024, 5, 29, 10, 0, 0, tzinfo=UTC)
    assert summary.instances_breakdown == {
        "radarr-4k": 2,
        "radarr-hd": 2,
        "sonarr-anime": 2,
        "sonarr-tv": 2,
    }
