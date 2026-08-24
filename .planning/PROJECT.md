# Arr-Oldies

## What This Is

Arr-Oldies is a CLI tool and auditing engine that connects to multiple Radarr and Sonarr instances to inventory all downloaded media files, correlate them with precise download and import event timestamps from the *arr History API, and list media files sorted by oldest downloads/imports. It allows self-hosters and media server administrators to inspect media age distribution, filter by audio language and explicit instance types, and safely execute targeted actions (deleting files, unmonitoring shows or individual episodes, or removing full library entries) with robust dry-run defaults.

## Core Value

Accurately inventory and trace media files across multiple Radarr and Sonarr instances back to their exact History API download/import timestamps, presenting an actionable, sortable audit with audio language filtering and safe, granular execution controls.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Multi-instance YAML configuration supporting multiple named Radarr and Sonarr instances (URL, API key, instance name, type)
- [ ] Config validation command (`arr-oldies validate-config`)
- [ ] Concurrent async client for Radarr (v3/v4) and Sonarr (v3/v4) endpoints with batch history pagination and instance resiliency
- [ ] Explicit instance selection flags (`--radarr`, `--sonarr`, `--instance <name>`)
- [ ] Deep History API inspection to extract exact `downloadFolderImported` and `grabbed` timestamps for movie and episode files
- [ ] Audio language extraction and filtering from media file `mediaInfo`
- [ ] Unified inventory catalog mapping media file IDs, file paths, sizes, audio languages, instances, and resolved historical timestamps
- [ ] Sorting and filtering CLI capabilities (sort by oldest import/download date, filter by audio language, instance, media type, size, date cutoff, limit)
- [ ] Rich terminal output formatting with structured tables, summary metrics, and optional JSON export
- [ ] Safe Action Engine with dry-run default:
  - `--delete`: Delete media file(s) via API
  - `--unmonitor`: Unmonitor movie or entire TV show
  - `--unmonitor-episode`: Unmonitor individual episode(s) without unmonitoring whole show
  - `--remove`: Remove complete library entry (movie or series) from *arr
  - Default dry-run mode (zero mutations unless `--execute` is specified)
  - Interactive confirmation required when `--execute` is used
  - `--yes` flag (when combined with `--execute`) to bypass confirmation for automation/cron jobs

### Out of Scope

- [ ] Automatic background deletion / daemon service — Arr-Oldies is an on-demand CLI tool, not a background daemon.
- [ ] Direct file system deletion bypassing *arr APIs — All file removals and unmonitor operations must be performed via Radarr/Sonarr APIs to keep *arr databases consistent.
- [ ] General *arr management UI / Web interface — Arr-Oldies is focused on CLI / terminal reporting and targeted cleanup.

## Context

- Self-hosted media servers often run multiple instances of Radarr (e.g. Radarr Standard, Radarr 4K/UHD, Radarr Anime) and Sonarr (e.g. Sonarr TV, Sonarr Anime, Sonarr 4K).
- As disks fill up, users need to know which media has been sitting on disk the longest since it was originally grabbed/imported.
- Users also maintain dual-audio or multi-language libraries and need to filter and clean/unmonitor items based on audio tracks (e.g., finding media missing localized audio or matching specific languages).
- Standard file system modification times can be inaccurate (metadata touching, migrations, transcode scripts). Querying `/api/v3/history` provides definitive history of when the media was actually imported into the library.

## Constraints

- **Tech stack**: Python 3.11+ (Rich, Typer, HTTPX, Pydantic v2, PyYAML)
- **Safety**: Dry-run by default; explicit `--execute` required for any mutation; confirmation prompt required unless `--yes` is specified.
- **API Compatibility**: Must support standard Radarr v3/v4 and Sonarr v3/v4 REST APIs.
- **History Requirement**: Strictly require History API events to resolve download/import timestamps.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Python with Rich + Typer + HTTPX | Fast development, rich terminal tables, excellent async I/O for querying multiple *arr instances concurrently | — Pending |
| Multi-instance YAML config | Clean, human-readable configuration for defining multiple named Radarr & Sonarr instances | — Pending |
| Explicit app filtering (--radarr / --sonarr) | Prevents unintended cross-app operations; requires clear targeting | — Pending |
| Granular action separation (--delete, --unmonitor, --unmonitor-episode, --remove) | Enables distinct workflows (cleanup files, unmonitor show, unmonitor single episode, purge entry) | — Pending |
| Audio language filtering | Inspects `mediaInfo` to filter by audio tracks | — Pending |
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
