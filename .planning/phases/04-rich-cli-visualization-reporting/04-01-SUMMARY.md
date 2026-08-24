---
phase: 04-rich-cli-visualization-reporting
plan: 01
subsystem: reporting
tags:
  - rich
  - formatters
  - table
  - summary-panel
requires:
  - phase: 03-unified-inventory-filtering-engine
    provides: MediaInventoryItem, InventorySummary, InventoryEngine
provides:
  - OutputFormat enum in arr_oldies.reporting.models
  - IEC binary size formatters, age tier styling, instance badges, and audio language badges in arr_oldies.reporting.formatters
  - Rich Table inventory rendering in arr_oldies.reporting.table
  - Storage metrics and space reclamation summary panel in arr_oldies.reporting.summary
affects:
  - src/arr_oldies/reporting/
key-files:
  created:
    - src/arr_oldies/reporting/models.py
    - src/arr_oldies/reporting/formatters.py
    - src/arr_oldies/reporting/table.py
    - src/arr_oldies/reporting/summary.py
    - src/arr_oldies/reporting/__init__.py
    - tests/test_formatters.py
    - tests/test_reporting_table.py
    - tests/test_reporting_summary.py
  modified: []
key-decisions:
  - "Adopted IEC binary scaling (KiB, MiB, GiB, TiB, PiB) with 2-decimal precision for human-readable file sizes."
  - "Structured age styling into 4 distinct color tiers (bold red for >=730d, yellow for >=365d, cyan for >=180d, green for <180d, dim for legacy) with contextual years/months annotations."
  - "Used rich.markup.escape in format_media_title to prevent bracket syntax injections (e.g. [1080p]) from breaking Rich markup."
  - "Designed render_summary_panel to compute potential space freed based on displayed/top-N items while retaining full library metrics."
requirements-completed:
  - CLI-01
  - CLI-02
duration: 4 min
completed: 2026-08-24T03:28:30Z
coverage:
  - deliverable: "IEC binary size formatter (format_size)"
    verification:
      kind: test
      ref: tests/test_formatters.py#test_format_size
      status: pass
    human_judgment: false
  - deliverable: "Color-coded age tiers and markup (get_age_color, format_age_markup)"
    verification:
      kind: test
      ref: tests/test_formatters.py#test_format_age_markup
      status: pass
    human_judgment: false
  - deliverable: "Instance badges and audio language markup"
    verification:
      kind: test
      ref: tests/test_formatters.py#test_format_instance_badge
      status: pass
    human_judgment: false
  - deliverable: "Rich table layout and limit captions (render_inventory_table)"
    verification:
      kind: test
      ref: tests/test_reporting_table.py#test_table_rendering_items
      status: pass
    human_judgment: false
  - deliverable: "Storage metrics and reclamation summary panel (render_summary_panel)"
    verification:
      kind: test
      ref: tests/test_reporting_summary.py#test_summary_panel_populated
      status: pass
    human_judgment: false
---

# Phase 04 Plan 01: Reporting Models, Formatters, Rich Inventory Table, and Summary Panel Summary

Implemented the core reporting and terminal visualization subsystem for Arr-Oldies in `src/arr_oldies/reporting/` providing IEC binary unit formatters, age tier styling, instance and audio language badges, responsive Rich `Table` layout, and storage metrics `Panel` summary cards.

## Accomplishments

1. **Reporting Models & Formatters (`models.py`, `formatters.py`)**:
   - Implemented `OutputFormat` enum (`table`, `json`).
   - Implemented `format_size` converting integer bytes to IEC binary units (`B`, `KiB`, `MiB`, `GiB`, `TiB`, `PiB`) with 2-decimal precision.
   - Implemented `get_age_color` and `format_age_markup` styling ages into bold red (2+ years), yellow (1-2 years), cyan (6-12 months), green (<6 months), and dim (legacy), with years/months contextual notations.
   - Implemented `format_instance_badge` (bold cyan for Radarr, bold magenta for Sonarr).
   - Implemented `format_audio_languages` (green for English, blue for Japanese, white for others).
   - Implemented `format_media_title` with bracket escaping via `rich.markup.escape`.

2. **Rich Inventory Table (`table.py`)**:
   - Implemented `render_inventory_table` creating an 8-column high-contrast Rich table (`#`, `Instance`, `Type`, `Title / Episode`, `Size`, `Import Date`, `Age`, `Audio`).
   - Added subtitle caption support for sliced results (`Showing top X of Y items`).

3. **Storage Metrics Summary Panel (`summary.py`, `__init__.py`)**:
   - Implemented `render_summary_panel` generating a multi-metric grid within a styled Rich `Panel`.
   - Displays total items (movie/episode split), total storage, date span in years/days, potential space freed (top-N candidate volume), legacy items count, and per-instance breakdowns.

4. **Testing & Verification**:
   - Created 13 unit tests across `tests/test_formatters.py`, `tests/test_reporting_table.py`, and `tests/test_reporting_summary.py`, passing with 100% green status.

## Deviations from Plan

None - plan executed exactly as written.

## Self-Check: PASSED
