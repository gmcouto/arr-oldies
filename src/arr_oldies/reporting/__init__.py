"""Reporting and visualization subsystem for Arr-Oldies."""

from arr_oldies.reporting.formatters import (
    format_age_markup,
    format_audio_languages,
    format_instance_badge,
    format_media_title,
    format_size,
    get_age_color,
)
from arr_oldies.reporting.json_export import build_json_payload, export_inventory_json
from arr_oldies.reporting.models import OutputFormat
from arr_oldies.reporting.summary import render_summary_panel
from arr_oldies.reporting.table import render_inventory_table

__all__ = [
    "OutputFormat",
    "build_json_payload",
    "export_inventory_json",
    "format_age_markup",
    "format_audio_languages",
    "format_instance_badge",
    "format_media_title",
    "format_size",
    "get_age_color",
    "render_inventory_table",
    "render_summary_panel",
]
