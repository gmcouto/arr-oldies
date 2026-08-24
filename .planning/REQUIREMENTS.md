# Requirements: Arr-Oldies

**Defined:** 2026-08-23
**Core Value:** Accurately inventory and trace media files across multiple Radarr and Sonarr instances back to their exact History API download/import timestamps, presenting an actionable, sortable audit with audio language filtering and safe, granular execution controls.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Configuration & Instances (CONF)

- [x] **CONF-01**: Parse YAML/JSON configuration defining multiple named Radarr and Sonarr instances (name, base URL, API key, service type)
- [ ] **CONF-02**: Provide `validate-config` CLI command to verify config syntax, connectivity, and authentication to all defined instances
- [ ] **CONF-03**: Support explicit instance filtering flags (`--radarr` to target all Radarr instances, `--sonarr` to target all Sonarr instances, `--instance <name>` to target a single specific instance)

### API Client & History Fetching (API)

- [ ] **API-01**: Async HTTPX client for Radarr v3/v4 endpoints (`/api/v3/movie`, `/api/v3/moviefile`, `/api/v3/history`, `/api/v3/history/movie`)
- [ ] **API-02**: Async HTTPX client for Sonarr v3/v4 endpoints (`/api/v3/series`, `/api/v3/episodefile`, `/api/v3/episode`, `/api/v3/history`, `/api/v3/history/series`)
- [ ] **API-03**: Batch history pagination with optimized page size (500–1000) and connection concurrency limits to avoid *arr SQLite database locks
- [ ] **API-04**: Resilient error handling per instance so unreachable or failing instances emit clear warnings without aborting scans of healthy instances

### Inventory & History Engine (INVT)

- [ ] **INVT-01**: Correlate media files (`movieFileId`, `episodeFileId`) with exact `downloadFolderImported` and `grabbed` timestamps from History API
- [ ] **INVT-02**: Extract and index `mediaInfo` audio languages for each media file
- [ ] **INVT-03**: Build unified media item inventory records (title, year/season/episode, file path, size, audio languages, instance, import date, grab date, age in days)
- [ ] **INVT-04**: Sort inventory items by oldest import date or oldest grab date
- [ ] **INVT-05**: Filter inventory items by audio language (`--audio-lang <lang>`), media type (movie vs episode), minimum size, and date/age cutoff
- [ ] **INVT-06**: Cleanly flag legacy media items that have no History API records without failing the scan

### CLI Reporting & Visualization (CLI)

- [ ] **CLI-01**: Format scan results in Rich terminal tables with color-coded age, instance badges, human-readable file sizes, and audio language tags
- [ ] **CLI-02**: Display summary metrics (total media items scanned, total storage consumed, date range spanned, potential space freed)
- [ ] **CLI-03**: Support `--limit <n>` to display top N oldest files
- [ ] **CLI-04**: Support `--format json` output for machine readability and scripting

### Safe Action Engine (ACT)

- [ ] **ACT-01**: Default to dry-run mode for all commands, printing exact simulated actions without mutating *arr databases or deleting files
- [ ] **ACT-02**: Implement `--delete` action to remove target media file(s) via Radarr/Sonarr API
- [ ] **ACT-03**: Implement `--unmonitor` action to unmonitor target movie or entire TV show in *arr without deleting files
- [ ] **ACT-04**: Implement `--unmonitor-episode` action to unmonitor specific individual episode(s) in Sonarr without unmonitoring the entire series
- [ ] **ACT-05**: Implement `--remove` action to completely remove the movie or show entry from the *arr library
- [ ] **ACT-06**: Require explicit `--execute` flag to perform write operations, prompting with an interactive Rich confirmation modal listing target files and space to be freed
- [ ] **ACT-07**: Support `--yes` flag (when combined with `--execute`) to bypass interactive confirmation for automated scripts and headless cron execution

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Export & Integrations

- **EXP-01**: CSV export format (`--format csv`)
- **EXP-02**: Discord / Telegram webhook notifications on cleanup execution
- **EXP-03**: Interactive TUI (Terminal User Interface) built with Textual for interactive checkbox selection and browsing

## Out of Scope

| Feature | Reason |
|---------|--------|
| Direct OS filesystem deletion | Causes database desynchronization with Radarr and Sonarr; triggers automated re-downloads if monitored |
| Unattended background daemon | High risk of accidental automated data loss; Arr-Oldies is an on-demand CLI tool |
| Web UI / Dashboard | Adds unnecessary web server complexity and frontend maintenance overhead; CLI-first focus |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| CONF-01 | Phase 1 | Complete |
| CONF-02 | Phase 1 | Pending |
| CONF-03 | Phase 1 | Pending |
| API-01 | Phase 2 | Pending |
| API-02 | Phase 2 | Pending |
| API-03 | Phase 2 | Pending |
| API-04 | Phase 2 | Pending |
| INVT-01 | Phase 3 | Pending |
| INVT-02 | Phase 3 | Pending |
| INVT-03 | Phase 3 | Pending |
| INVT-04 | Phase 3 | Pending |
| INVT-05 | Phase 3 | Pending |
| INVT-06 | Phase 3 | Pending |
| CLI-01 | Phase 4 | Pending |
| CLI-02 | Phase 4 | Pending |
| CLI-03 | Phase 4 | Pending |
| CLI-04 | Phase 4 | Pending |
| ACT-01 | Phase 5 | Pending |
| ACT-02 | Phase 5 | Pending |
| ACT-03 | Phase 5 | Pending |
| ACT-04 | Phase 5 | Pending |
| ACT-05 | Phase 5 | Pending |
| ACT-06 | Phase 5 | Pending |
| ACT-07 | Phase 5 | Pending |

**Coverage:**

- v1 requirements: 24 total
- Mapped to phases: 24
- Unmapped: 0 ✓

---
*Requirements defined: 2026-08-23*
*Last updated: 2026-08-23 after initial definition*
