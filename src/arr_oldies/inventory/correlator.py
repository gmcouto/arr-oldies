"""History API timestamp correlation engine for Radarr and Sonarr libraries."""

from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

from arr_oldies.api.fetcher import InstanceMediaData
from arr_oldies.api.models import (
    RadarrHistoryRecord,
    RadarrMovie,
    RadarrMovieFile,
    SonarrEpisode,
    SonarrEpisodeFile,
    SonarrHistoryRecord,
    SonarrSeries,
)
from arr_oldies.inventory.languages import LanguageNormalizer
from arr_oldies.inventory.models import HistoryStatus, MediaInventoryItem, MediaType
from arr_oldies.models import InstanceType


class RadarrHistoryIndex:
    """In-memory multi-key hash index for Radarr history records (O(N+M) lookup)."""

    def __init__(self, records: list[RadarrHistoryRecord | Any]) -> None:
        self.imports_by_file_id: dict[int, list[RadarrHistoryRecord]] = defaultdict(list)
        self.imports_by_path: dict[str, list[RadarrHistoryRecord]] = defaultdict(list)
        self.imports_by_movie_id: dict[int, list[RadarrHistoryRecord]] = defaultdict(list)
        self.grabs_by_download_id: dict[str, RadarrHistoryRecord] = {}
        self.grabs_by_movie_id: dict[int, list[RadarrHistoryRecord]] = defaultdict(list)

        for record in records:
            event_type = record.event_type.lower() if record.event_type else ""
            if event_type in ("downloadfolderimported", "moviefileimported", "imported", "3"):
                file_id_raw = (
                    record.data.get("fileId")
                    or record.data.get("movieFileId")
                    or record.data.get("file_id")
                    or record.data.get("movie_file_id")
                )
                if file_id_raw is not None:
                    try:
                        self.imports_by_file_id[int(file_id_raw)].append(record)
                    except (ValueError, TypeError):
                        pass

                imported_path = (
                    record.data.get("importedPath")
                    or record.data.get("path")
                    or record.data.get("imported_path")
                )
                if imported_path:
                    self.imports_by_path[str(imported_path).strip().lower()].append(record)

                if record.movie_id:
                    self.imports_by_movie_id[record.movie_id].append(record)

            elif event_type in ("grabbed", "1", "grab"):
                if record.download_id:
                    self.grabs_by_download_id[record.download_id] = record
                if record.movie_id:
                    self.grabs_by_movie_id[record.movie_id].append(record)


class SonarrHistoryIndex:
    """In-memory multi-key hash index for Sonarr history records (O(N+M) lookup)."""

    def __init__(self, records: list[SonarrHistoryRecord | Any]) -> None:
        self.imports_by_file_id: dict[int, list[SonarrHistoryRecord]] = defaultdict(list)
        self.imports_by_episode_id: dict[int, list[SonarrHistoryRecord]] = defaultdict(list)
        self.imports_by_path: dict[str, list[SonarrHistoryRecord]] = defaultdict(list)
        self.grabs_by_download_id: dict[str, SonarrHistoryRecord] = {}
        self.grabs_by_episode_id: dict[int, list[SonarrHistoryRecord]] = defaultdict(list)
        self.grabs_by_series_id: dict[int, list[SonarrHistoryRecord]] = defaultdict(list)

        for record in records:
            event_type = record.event_type.lower() if record.event_type else ""
            if event_type in ("downloadfolderimported", "episodefileimported", "imported", "3"):
                file_id_raw = (
                    record.data.get("fileId")
                    or record.data.get("episodeFileId")
                    or record.data.get("file_id")
                    or record.data.get("episode_file_id")
                )
                if file_id_raw is not None:
                    try:
                        self.imports_by_file_id[int(file_id_raw)].append(record)
                    except (ValueError, TypeError):
                        pass

                imported_path = (
                    record.data.get("importedPath")
                    or record.data.get("path")
                    or record.data.get("imported_path")
                )
                if imported_path:
                    self.imports_by_path[str(imported_path).strip().lower()].append(record)

                if record.episode_id:
                    self.imports_by_episode_id[record.episode_id].append(record)

            elif event_type in ("grabbed", "1", "grab"):
                if record.download_id:
                    self.grabs_by_download_id[record.download_id] = record
                if record.episode_id:
                    self.grabs_by_episode_id[record.episode_id].append(record)
                if record.series_id:
                    self.grabs_by_series_id[record.series_id].append(record)


class HistoryCorrelator:
    """Correlates media files with History API events and standardizes inventory items."""

    def __init__(self, normalizer: LanguageNormalizer | None = None) -> None:
        self.normalizer = normalizer or LanguageNormalizer()

    def correlate_instance(
        self,
        instance_data: InstanceMediaData,
        reference_time: datetime | None = None,
    ) -> list[MediaInventoryItem]:
        """Correlate all media files from an instance into MediaInventoryItem records."""
        now_utc = reference_time or datetime.now(UTC)
        if now_utc.tzinfo is None:
            now_utc = now_utc.replace(tzinfo=UTC)
        else:
            now_utc = now_utc.astimezone(UTC)

        if instance_data.instance_type == InstanceType.RADARR:
            return self._correlate_radarr(instance_data, now_utc)
        elif instance_data.instance_type == InstanceType.SONARR:
            return self._correlate_sonarr(instance_data, now_utc)
        else:
            raise ValueError(f"Unsupported instance type: '{instance_data.instance_type}'")

    def _correlate_radarr(
        self,
        instance_data: InstanceMediaData,
        now_utc: datetime,
    ) -> list[MediaInventoryItem]:
        """Correlate Radarr movie files with history events or fallback to date_added."""
        movies_by_id: dict[int, RadarrMovie] = {m.id: m for m in instance_data.movies}
        index = RadarrHistoryIndex(instance_data.history_records)
        items: list[MediaInventoryItem] = []

        for movie_file in instance_data.movie_files:
            movie = movies_by_id.get(movie_file.movie_id)
            title = movie.title if movie else (movie_file.relative_path or f"Movie {movie_file.movie_id}")
            year = movie.year if movie else None

            # Audio languages extraction
            raw_audio = movie_file.media_info.audio_languages if movie_file.media_info else None
            audio_languages = self.normalizer.extract_languages(raw_audio) if movie_file.media_info else []
            video_codec = movie_file.media_info.video_codec if movie_file.media_info else None
            resolution = movie_file.media_info.resolution if movie_file.media_info else None

            # 1. Match import event
            candidate_imports: list[RadarrHistoryRecord] = []
            if movie_file.id in index.imports_by_file_id:
                candidate_imports = index.imports_by_file_id[movie_file.id]
            elif movie_file.path and movie_file.path.strip().lower() in index.imports_by_path:
                candidate_imports = index.imports_by_path[movie_file.path.strip().lower()]
            elif movie_file.movie_id in index.imports_by_movie_id:
                candidate_imports = index.imports_by_movie_id[movie_file.movie_id]

            if candidate_imports:
                # Pick newest import event matching this file
                import_event = max(candidate_imports, key=lambda r: r.date)
                import_date = import_event.date
                download_id = import_event.download_id
                source_title = import_event.source_title
                has_history = True
                is_legacy = False

                # Correlate grab event
                grab_event: RadarrHistoryRecord | None = None
                if download_id and download_id in index.grabs_by_download_id:
                    grab_event = index.grabs_by_download_id[download_id]
                else:
                    movie_grabs = [
                        r for r in index.grabs_by_movie_id.get(movie_file.movie_id, [])
                        if r.date <= import_date
                    ]
                    if movie_grabs:
                        grab_event = max(movie_grabs, key=lambda r: r.date)

                if grab_event:
                    grab_date = grab_event.date
                    history_status = HistoryStatus.GRABBED_AND_IMPORTED
                    if not source_title and grab_event.source_title:
                        source_title = grab_event.source_title
                else:
                    grab_date = None
                    history_status = HistoryStatus.IMPORTED
            else:
                # Legacy fallback per INVT-06
                import_date = movie_file.date_added
                grab_date = None
                has_history = False
                is_legacy = True
                history_status = HistoryStatus.LEGACY
                download_id = None
                source_title = None

            # Calculate age in days
            if import_date.tzinfo is None:
                import_date_utc = import_date.replace(tzinfo=UTC)
            else:
                import_date_utc = import_date.astimezone(UTC)
            age_days = max(0, (now_utc - import_date_utc).days)

            item = MediaInventoryItem(
                id=f"{instance_data.instance_name}:{movie_file.id}",
                instance_name=instance_data.instance_name,
                instance_type=instance_data.instance_type,
                media_type=MediaType.MOVIE,
                title=title,
                year=year,
                movie_id=movie_file.movie_id,
                movie_file_id=movie_file.id,
                file_path=movie_file.path,
                relative_path=movie_file.relative_path,
                size_bytes=movie_file.size,
                audio_languages=audio_languages,
                raw_audio_languages=raw_audio,
                video_codec=video_codec,
                resolution=resolution,
                import_date=import_date,
                grab_date=grab_date,
                age_days=age_days,
                has_history=has_history,
                is_legacy=is_legacy,
                history_status=history_status,
                source_title=source_title,
                download_id=download_id,
            )
            items.append(item)

        return items

    def _correlate_sonarr(
        self,
        instance_data: InstanceMediaData,
        now_utc: datetime,
    ) -> list[MediaInventoryItem]:
        """Correlate Sonarr episode files with history events or fallback to date_added."""
        series_by_id: dict[int, SonarrSeries] = {s.id: s for s in instance_data.series}
        episodes_by_file_id: dict[int, list[SonarrEpisode]] = defaultdict(list)
        for ep in instance_data.episodes:
            if ep.episode_file_id is not None:
                episodes_by_file_id[ep.episode_file_id].append(ep)

        index = SonarrHistoryIndex(instance_data.history_records)
        items: list[MediaInventoryItem] = []

        for ep_file in instance_data.episode_files:
            series = series_by_id.get(ep_file.series_id)
            title = series.title if series else (ep_file.relative_path or f"Series {ep_file.series_id}")
            year = series.year if series else None

            episodes = episodes_by_file_id.get(ep_file.id, [])
            ep_numbers = sorted(e.episode_number for e in episodes)
            ep_ids = [e.id for e in episodes]

            if len(ep_numbers) > 1:
                formatted_episode = f"S{ep_file.season_number:02d}E{ep_numbers[0]:02d}-E{ep_numbers[-1]:02d}"
            elif ep_numbers:
                formatted_episode = f"S{ep_file.season_number:02d}E{ep_numbers[0]:02d}"
            else:
                formatted_episode = f"S{ep_file.season_number:02d}"

            episode_title = episodes[0].title if (len(episodes) == 1 and episodes[0].title) else None

            # Audio languages extraction
            raw_audio = ep_file.media_info.audio_languages if ep_file.media_info else None
            audio_languages = self.normalizer.extract_languages(raw_audio) if ep_file.media_info else []
            video_codec = ep_file.media_info.video_codec if ep_file.media_info else None
            resolution = ep_file.media_info.resolution if ep_file.media_info else None

            # 1. Match import event
            candidate_imports: list[SonarrHistoryRecord] = []
            if ep_file.id in index.imports_by_file_id:
                candidate_imports = index.imports_by_file_id[ep_file.id]
            elif ep_file.path and ep_file.path.strip().lower() in index.imports_by_path:
                candidate_imports = index.imports_by_path[ep_file.path.strip().lower()]
            elif ep_ids:
                for eid in ep_ids:
                    candidate_imports.extend(index.imports_by_episode_id.get(eid, []))

            if candidate_imports:
                import_event = max(candidate_imports, key=lambda r: r.date)
                import_date = import_event.date
                download_id = import_event.download_id
                source_title = import_event.source_title
                has_history = True
                is_legacy = False
                if not ep_ids and import_event.episode_id:
                    ep_ids = [import_event.episode_id]


                # Correlate grab event
                grab_event: SonarrHistoryRecord | None = None
                if download_id and download_id in index.grabs_by_download_id:
                    grab_event = index.grabs_by_download_id[download_id]
                elif ep_ids:
                    candidate_grabs: list[SonarrHistoryRecord] = []
                    for eid in ep_ids:
                        candidate_grabs.extend(index.grabs_by_episode_id.get(eid, []))
                    valid_grabs = [r for r in candidate_grabs if r.date <= import_date]
                    if valid_grabs:
                        grab_event = max(valid_grabs, key=lambda r: r.date)
                    else:
                        series_grabs = [
                            r for r in index.grabs_by_series_id.get(ep_file.series_id, [])
                            if r.date <= import_date
                        ]
                        if series_grabs:
                            grab_event = max(series_grabs, key=lambda r: r.date)
                else:
                    series_grabs = [
                        r for r in index.grabs_by_series_id.get(ep_file.series_id, [])
                        if r.date <= import_date
                    ]
                    if series_grabs:
                        grab_event = max(series_grabs, key=lambda r: r.date)

                if grab_event:
                    grab_date = grab_event.date
                    history_status = HistoryStatus.GRABBED_AND_IMPORTED
                    if not source_title and grab_event.source_title:
                        source_title = grab_event.source_title
                else:
                    grab_date = None
                    history_status = HistoryStatus.IMPORTED
            else:
                # Legacy fallback per INVT-06
                import_date = ep_file.date_added
                grab_date = None
                has_history = False
                is_legacy = True
                history_status = HistoryStatus.LEGACY
                download_id = None
                source_title = None

            # Calculate age in days
            if import_date.tzinfo is None:
                import_date_utc = import_date.replace(tzinfo=UTC)
            else:
                import_date_utc = import_date.astimezone(UTC)
            age_days = max(0, (now_utc - import_date_utc).days)

            item = MediaInventoryItem(
                id=f"{instance_data.instance_name}:{ep_file.id}",
                instance_name=instance_data.instance_name,
                instance_type=instance_data.instance_type,
                media_type=MediaType.EPISODE,
                title=title,
                year=year,
                season_number=ep_file.season_number,
                episode_numbers=ep_numbers,
                formatted_episode=formatted_episode,
                episode_title=episode_title,
                series_id=ep_file.series_id,
                episode_file_id=ep_file.id,
                episode_ids=ep_ids,
                file_path=ep_file.path,
                relative_path=ep_file.relative_path,
                size_bytes=ep_file.size,
                audio_languages=audio_languages,
                raw_audio_languages=raw_audio,
                video_codec=video_codec,
                resolution=resolution,
                import_date=import_date,
                grab_date=grab_date,
                age_days=age_days,
                has_history=has_history,
                is_legacy=is_legacy,
                history_status=history_status,
                source_title=source_title,
                download_id=download_id,
            )
            items.append(item)

        return items
