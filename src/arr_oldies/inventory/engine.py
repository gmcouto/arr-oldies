"""Inventory processing engine: composable filtering, deterministic sorting, and metrics generation."""

from datetime import UTC
from typing import Any

from arr_oldies.inventory.languages import LanguageNormalizer
from arr_oldies.inventory.models import (
    InventoryFilter,
    InventorySummary,
    MediaInventoryItem,
    MediaType,
    SortDirection,
    SortKey,
)


class InventoryEngine:
    """Orchestrates inventory filtering, sorting, and aggregate summary generation."""

    def __init__(self, normalizer: LanguageNormalizer | None = None) -> None:
        self.normalizer = normalizer or LanguageNormalizer()

    def filter_inventory(
        self,
        items: list[MediaInventoryItem],
        criteria: InventoryFilter,
    ) -> list[MediaInventoryItem]:
        """Filter media inventory items matching all specified criteria in a single pass."""
        filtered: list[MediaInventoryItem] = []

        # Precompute normalized instance names if provided
        norm_instances: set[str] | None = None
        if criteria.instance_names:
            norm_instances = {n.strip().lower() for n in criteria.instance_names}

        # Ensure before_date and after_date are UTC
        before_date = criteria.before_date
        if before_date is not None:
            if before_date.tzinfo is None:
                before_date = before_date.replace(tzinfo=UTC)
            else:
                before_date = before_date.astimezone(UTC)

        after_date = criteria.after_date
        if after_date is not None:
            if after_date.tzinfo is None:
                after_date = after_date.replace(tzinfo=UTC)
            else:
                after_date = after_date.astimezone(UTC)

        for item in items:
            # 1. Media Type Filter
            if criteria.media_types and item.media_type not in criteria.media_types:
                continue

            # 2. Instance Filter
            if (
                norm_instances is not None
                and item.instance_name.strip().lower() not in norm_instances
            ):
                continue

            # 3. Size Bounds Filter (bytes)
            if criteria.min_size_bytes is not None and item.size_bytes < criteria.min_size_bytes:
                continue
            if criteria.max_size_bytes is not None and item.size_bytes > criteria.max_size_bytes:
                continue

            # 4. Age Bounds Filter (days)
            if criteria.min_age_days is not None and item.age_days < criteria.min_age_days:
                continue
            if criteria.max_age_days is not None and item.age_days > criteria.max_age_days:
                continue

            # 5. Date Bounds Filter
            if before_date is not None and item.import_date >= before_date:
                continue
            if after_date is not None and item.import_date <= after_date:
                continue

            # 6. Legacy / History Filter
            if criteria.legacy_only and item.has_history:
                continue
            if criteria.history_only and not item.has_history:
                continue

            # 7. Monitored / Unmonitored Filter
            if criteria.monitored_only and not item.monitored:
                continue
            if criteria.unmonitored_only and item.monitored:
                continue

            # 8. Audio Language Filter (Positive)
            if criteria.audio_langs and not any(
                self.normalizer.matches(item.audio_languages, q) for q in criteria.audio_langs
            ):
                continue

            # 9. Negative Audio Language Filter (INVT-07)
            if criteria.not_audio_langs and any(
                self.normalizer.matches(item.audio_languages, q) for q in criteria.not_audio_langs
            ):
                continue

            # 10. Title Substring Filter (INVT-08)
            if criteria.titles:
                title_queries = [t.strip().lower() for t in criteria.titles if t.strip()]
                if title_queries:
                    item_title_lower = item.title.lower()
                    item_ep_title_lower = (
                        item.episode_title.lower() if item.episode_title else ""
                    )
                    matched_title = any(
                        q in item_title_lower or (item_ep_title_lower and q in item_ep_title_lower)
                        for q in title_queries
                    )
                    if not matched_title:
                        continue

            # 11. Tag Inclusion Filter (INVT-09)
            if criteria.tags:
                tag_queries = [q.strip().lower() for q in criteria.tags if q.strip()]
                if tag_queries:
                    item_tags = {t.strip().lower() for t in item.tags}
                    if not any(q in item_tags for q in tag_queries):
                        continue

            # 12. Tag Exclusion Filter (INVT-09)
            if criteria.not_tags:
                not_tag_queries = [q.strip().lower() for q in criteria.not_tags if q.strip()]
                if not_tag_queries:
                    item_tags = {t.strip().lower() for t in item.tags}
                    if any(q in item_tags for q in not_tag_queries):
                        continue

            filtered.append(item)

        return filtered

    def sort_inventory(
        self,
        items: list[MediaInventoryItem],
        sort_key: SortKey = SortKey.IMPORT_DATE,
        direction: SortDirection = SortDirection.ASC,
    ) -> list[MediaInventoryItem]:
        """Sort inventory items deterministically with stable tie-breaking."""
        reverse = direction == SortDirection.DESC

        def _sort_extractor(item: MediaInventoryItem) -> tuple[Any, ...]:
            if sort_key == SortKey.IMPORT_DATE:
                return (item.import_date, item.title.lower(), item.id)
            elif sort_key == SortKey.GRAB_DATE:
                # Fallback to import_date if grab_date is None
                return (item.grab_date or item.import_date, item.title.lower(), item.id)
            elif sort_key == SortKey.SIZE:
                return (item.size_bytes, item.import_date, item.title.lower(), item.id)
            elif sort_key == SortKey.TITLE:
                return (item.title.lower(), item.import_date, item.id)
            elif sort_key == SortKey.AGE:
                return (item.age_days, item.title.lower(), item.id)
            return (item.import_date, item.title.lower(), item.id)

        return sorted(items, key=_sort_extractor, reverse=reverse)

    def generate_summary(self, items: list[MediaInventoryItem]) -> InventorySummary:
        """Compute aggregate summary metrics across inventory items."""
        if not items:
            return InventorySummary()

        total_size = sum(item.size_bytes for item in items)
        movies = sum(1 for item in items if item.media_type == MediaType.MOVIE)
        episodes = sum(1 for item in items if item.media_type == MediaType.EPISODE)
        legacy = sum(1 for item in items if item.is_legacy)

        import_dates = [item.import_date for item in items]
        grab_dates = [item.grab_date for item in items if item.grab_date is not None]

        instances_breakdown: dict[str, int] = {}
        for item in items:
            instances_breakdown[item.instance_name] = (
                instances_breakdown.get(item.instance_name, 0) + 1
            )

        return InventorySummary(
            total_items=len(items),
            total_size_bytes=total_size,
            movie_count=movies,
            episode_count=episodes,
            legacy_count=legacy,
            oldest_import_date=min(import_dates) if import_dates else None,
            newest_import_date=max(import_dates) if import_dates else None,
            oldest_grab_date=min(grab_dates) if grab_dates else None,
            instances_breakdown=instances_breakdown,
        )
