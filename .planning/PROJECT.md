# Arr-Oldies

## What This Is

Arr-Oldies is a CLI tool and auditing engine that connects to multiple Radarr and Sonarr instances to inventory all downloaded media files, correlate them with precise download and import event timestamps from the *arr History API, and list media files sorted by oldest downloads/imports. It allows self-hosters and media server administrators to identify stale media, understand storage age distribution across instances, and safely perform cleanup actions (deletion and unmonitoring) with safe dry-run defaults.

## Core Value

Accurately inventory and trace media files across multiple Radarr and Sonarr instances back to their exact History API download/import timestamps, presenting an actionable, sortable audit of oldest files with safe execution controls.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Multi-instance configuration (YAML/JSON) supporting multiple Radarr and Sonarr instances (URL, API key, instance name, type)
- [ ] Concurrent client / API connector for Radarr (v3/v4) and Sonarr (v3/v4) endpoints
- [ ] Deep History API inspection to extract exact `downloadFolderImported` and `grabbed` timestamps for movie and episode files
- [ ] File inventory cataloging mapping media file IDs, file paths, sizes, quality profiles, instances, and resolved historical timestamps
- [ ] Sorting and filtering CLI capabilities (sort by oldest import / download date, filter by instance, media type, size, date cutoff, limit results)
- [ ] Rich terminal output formatting with structured tables, summary metrics (total size, date ranges), and optional JSON export
- [ ] Safe action engine for file deletion and media unmonitoring in Radarr/Sonarr:
  - Default dry-run mode (no destructive changes)
  - Interactive confirmation required when `--execute` is supplied
  - Non-interactive `--yes` flag (when combined with `--execute`) for automated scripting/cron jobs

### Out of Scope

- [ ] Automatic background deletion / daemon service — Arr-Oldies is an on-demand CLI tool, not a background daemon.
- [ ] Direct file system deletion bypassing *arr APIs — All file removals and unmonitor operations must be performed via Radarr/Sonarr APIs to keep *arr databases consistent.
- [ ] General *arr management UI / Web interface — Arr-Oldies is focused on CLI / terminal reporting and targeted cleanup.

## Context

- Self-hosted media servers often run multiple instances of Radarr (e.g. Radarr Standard, Radarr 4K/UHD, Radarr Anime) and Sonarr (e.g. Sonarr TV, Sonarr Anime, Sonarr 4K).
- As disks fill up, users need to know which media has been sitting on disk the longest since it was originally grabbed/imported.
- Standard file system modification times can be inaccurate (metadata touching, migrations, transcode scripts). Querying `/api/v3/history` provides definitive history of when the media was actually imported into the library.

## Constraints

- **Tech stack**: Python 3.10+ (Rich, Typer, HTTPX, Pydantic, PyYAML)
- **Safety**: Dry-run by default; explicit `--execute` required for any mutation; confirmation prompt required unless `--yes` is specified.
- **API Compatibility**: Must support standard Radarr v3/v4 and Sonarr v3/v4 REST APIs.
- **History Requirement**: Strictly require History API events to resolve download/import timestamps.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Python with Rich + Typer + HTTPX | Fast development, rich terminal tables, excellent async I/O for querying multiple *arr instances concurrently | — Pending |
| Multi-instance YAML config | Clean, human-readable configuration for defining multiple named Radarr & Sonarr instances | — Pending |
| Strict History API dates | Ensures true download/import event dates rather than arbitrary filesystem timestamps | — Pending |
| Dry-run default with --execute and --yes | Prevents accidental data loss; safe for both interactive exploration and headless cron jobs | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-08-23 after initialization*
