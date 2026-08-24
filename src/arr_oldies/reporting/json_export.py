"""Structured JSON export serialization for media inventory scan results."""

import json
from datetime import UTC, datetime
from typing import Any

from arr_oldies import __version__
from arr_oldies.inventory.models import InventorySummary, MediaInventoryItem, SortDirection, SortKey
from arr_oldies.reporting.formatters import format_size


def build_json_payload(
    items: list[MediaInventoryItem],
    summary: InventorySummary,
    target_instances: list[str],
    total_scanned: int,
    limit: int | None = None,
    sort_key: SortKey = SortKey.IMPORT_DATE,
    sort_direction: SortDirection = SortDirection.ASC,
) -> dict[str, Any]:
    """Construct structured JSON payload combining metadata, summary metrics, and item records."""
    displayed_items = items[:limit] if limit else items
    displayed_size = sum(item.size_bytes for item in displayed_items)

    span_days = 0
    if summary.oldest_import_date and summary.newest_import_date:
        span_days = max(0, (summary.newest_import_date - summary.oldest_import_date).days)

    metadata: dict[str, Any] = {
        "version": __version__,
        "scanned_at": datetime.now(UTC).isoformat(),
        "target_instances": target_instances,
        "total_scanned_items": total_scanned,
        "total_matched_items": len(items),
        "displayed_items": len(displayed_items),
        "limit": limit,
        "sort_key": sort_key.value,
        "sort_direction": sort_direction.value,
    }

    summary_data: dict[str, Any] = {
        "total_items": summary.total_items,
        "total_size_bytes": summary.total_size_bytes,
        "total_size_human": format_size(summary.total_size_bytes),
        "movie_count": summary.movie_count,
        "episode_count": summary.episode_count,
        "legacy_count": summary.legacy_count,
        "oldest_import_date": (
            summary.oldest_import_date.isoformat() if summary.oldest_import_date else None
        ),
        "newest_import_date": (
            summary.newest_import_date.isoformat() if summary.newest_import_date else None
        ),
        "date_range_spanned_days": span_days,
        "potential_space_freed_bytes": displayed_size,
        "potential_space_freed_human": format_size(displayed_size),
        "instances_breakdown": summary.instances_breakdown,
    }

    item_records: list[dict[str, Any]] = []
    for item in displayed_items:
        dumped = item.model_dump(mode="json")
        dumped["size_human"] = format_size(item.size_bytes)
        item_records.append(dumped)

    return {
        "metadata": metadata,
        "summary": summary_data,
        "items": item_records,
    }


def export_inventory_json(
    items: list[MediaInventoryItem],
    summary: InventorySummary,
    target_instances: list[str],
    total_scanned: int,
    limit: int | None = None,
    sort_key: SortKey = SortKey.IMPORT_DATE,
    sort_direction: SortDirection = SortDirection.ASC,
    indent: int = 2,
) -> str:
    """Serialize scan results to clean, formatted JSON string."""
    payload = build_json_payload(
        items=items,
        summary=summary,
        target_instances=target_instances,
        total_scanned=total_scanned,
        limit=limit,
        sort_key=sort_key,
        sort_direction=sort_direction,
    )
    return json.dumps(payload, indent=indent, default=str)
