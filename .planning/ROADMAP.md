# Roadmap: Arr-Oldies

## Overview

Arr-Oldies delivers a high-performance CLI tool to audit and clean stale media files across multiple Radarr and Sonarr instances. The roadmap progresses slice-by-slice in vertical MVP mode: starting from configuration and multi-instance connectivity, building robust async API clients, implementing the History API correlation engine and audio language extraction, delivering Rich CLI table reporting, and culminating in a guarded, safe action engine for file deletion, episode/show unmonitoring, and library entry removal.

## Phases

**Phase Numbering:**

- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Foundation, Multi-Instance Configuration & CLI Scaffolding** - Establish project foundation, Pydantic schemas, YAML config loading, validation command, and base CLI (completed 2026-08-23)
- [x] **Phase 2: Async *arr API Clients & Batch History Fetcher** - Build HTTPX async clients for Radarr v3/v4 and Sonarr v3/v4 with batch history pagination and instance resilience (completed 2026-08-23)
- [x] **Phase 3: Media Inventory & History Timestamp Correlator** - Correlate media files with History API import/grab timestamps, extract audio languages, and build sortable/filterable inventory (completed 2026-08-24)
- [x] **Phase 4: Rich CLI Visualization & Reporting** - Implement Rich terminal table formatting, storage metrics summaries, output limits, and JSON export (completed 2026-08-24)
- [x] **Phase 6: Support Composite Time Formats for Age Filters** - Support compound relative time duration strings (e.g., `1y1m1d` for 1 year, 1 month, and 1 day) in `--older-than` and `--newer-than` filters (completed 2026-08-24)
- [x] **Phase 7: Scope unmonitor to episodes and add unmonitor-series option** - Scope unmonitor to individual media items and add full series unmonitoring option (completed 2026-08-24)
- [x] **Phase 8: Support --monitored and --unmonitored filter for scan and clean** - Filter inventory by monitored status to inspect or unmonitor only monitored items (completed 2026-08-24)
- [ ] **Phase 9: Docker Packaging and GitHub Actions Release Workflow** - Containerize arr-oldies and automate multi-platform Docker image build/publish to GHCR upon version release tags

## Phase Details

### Phase 1: Foundation, Multi-Instance Configuration & CLI Scaffolding

**Goal**: Establish project foundation, Pydantic schemas, YAML config loading, validation command, and base CLI
**Mode:** mvp
**Depends on**: Nothing (first phase)
**Requirements**: CONF-01, CONF-02, CONF-03
**Success Criteria** (what must be TRUE):

  1. User can define multiple Radarr and Sonarr instances in a `config.yaml` file.
  2. User can execute `arr-oldies validate-config` to verify connection and auth against each configured instance.
  3. User can target explicit instances or service types using `--radarr`, `--sonarr`, and `--instance <name>` flags.

**Plans**: 2/2 plans executed

Plans:
**Wave 1**

- [x] 01-01-PLAN.md: Project Foundation, Models & Configuration Loader

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 01-02-PLAN.md: Instance Targeting, Health Prober & CLI Validation Command

### Phase 2: Async *arr API Clients & Batch History Fetcher

**Goal**: Build HTTPX async clients for Radarr v3/v4 and Sonarr v3/v4 with batch history pagination and instance resilience
**Mode:** mvp
**Depends on**: Phase 1
**Requirements**: API-01, API-02, API-03, API-04
**Success Criteria** (what must be TRUE):

  1. `RadarrClient` and `SonarrClient` concurrently fetch movies, series, episode files, and history records.
  2. History API queries use optimized batch pagination (500–1000 items/page) to prevent *arr database lock timeouts.
  3. Unreachable or failing instances log warnings gracefully without terminating scans of healthy instances.

**Plans**: 2/2 plans executed

Plans:
**Wave 1**

- [x] 02-01-PLAN.md: Base Async Client, API Models & Resilience Infrastructure

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 02-02-PLAN.md: Radarr & Sonarr Clients, Batch History Pagination & Resilient Multi-Instance Fetcher

### Phase 3: Media Inventory & History Timestamp Correlator

**Goal**: Correlate media files with History API import/grab timestamps, extract audio languages, and build sortable/filterable inventory
**Mode:** mvp
**Depends on**: Phase 2
**Requirements**: INVT-01, INVT-02, INVT-03, INVT-04, INVT-05, INVT-06
**Success Criteria** (what must be TRUE):

  1. Media files are accurately correlated with their exact `downloadFolderImported` / `grabbed` timestamps from History API.
  2. Audio languages are extracted from media file `mediaInfo` and filterable via `--audio-lang`.
  3. Inventory items are sorted oldest-first with multi-dimensional filtering (date cutoff, size, instance, media type).
  4. Media files without history events are cleanly flagged as unindexed without failing the scan.

**Plans**: 2/2 plans executed planned

Plans:
**Wave 1**

- [x] 03-01-PLAN.md: Core Inventory Models, ISO-639 Language Normalization & Human Unit Parsers

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 03-02-PLAN.md: Hash-Indexed History Correlator, Legacy Fallback & Inventory Processing Engine

### Phase 4: Rich CLI Visualization & Reporting

**Goal**: Implement Rich terminal table formatting, storage metrics summaries, output limits, and JSON export
**Mode:** mvp
**Depends on**: Phase 3
**Requirements**: CLI-01, CLI-02, CLI-03, CLI-04
**Success Criteria** (what must be TRUE):

  1. Running `arr-oldies scan` renders a high-contrast Rich table of oldest files with age, size, instance, and audio language badges.
  2. Output includes summary cards detailing total storage inspected, oldest items date range, and potential space freed.
  3. Output can be constrained with `--limit <n>` or exported as structured JSON via `--format json`.

**Plans**: TBD

Plans:

- [x] 04-01-PLAN.md
- [x] 04-02-PLAN.md

**Wave 1**

- [x] 04-01: Rich table visualizer with color-coded age tiers, units formatting, and summary cards

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 04-02: CLI scan command integration with sorting/filtering flags and JSON serialization

### Phase 5: Safe Action Engine (Dry-Run, Deletion & Unmonitoring)

**Goal**: Build safe mutation pipeline with dry-run default, `--delete`, `--unmonitor`, `--unmonitor-episode`, `--remove`, and confirmation guards
**Mode:** mvp
**Depends on**: Phase 4
**Requirements**: ACT-01, ACT-02, ACT-03, ACT-04, ACT-05, ACT-06, ACT-07
**Success Criteria** (what must be TRUE):

  1. All cleanup commands default to dry-run simulation mode, displaying simulated changes without mutating *arr databases.
  2. User can execute file deletion (`--delete`), show unmonitoring (`--unmonitor`), single episode unmonitoring (`--unmonitor-episode`), or full library entry removal (`--remove`).
  3. Interactive execution (`--execute`) presents a Rich confirmation dialog before applying mutations.
  4. Headless scripts can execute non-interactively using `--execute --yes`.

**Plans**: 2/2 plans executed

Plans:
**Wave 1**

- [x] 05-01-PLAN.md: Action Models, API Client Mutation Endpoints & Ordered Executor Core

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 05-02-PLAN.md: Confirmation Modal, Interactive Prompt Guards & CLI Clean Command

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation, Multi-Instance Configuration & CLI Scaffolding | 2/2 | Complete    | 2026-08-23 |
| 2. Async *arr API Clients & Batch History Fetcher | 2/2 | Complete    | 2026-08-23 |
| 3. Media Inventory & History Timestamp Correlator | 2/2 | Complete    | 2026-08-24 |
| 4. Rich CLI Visualization & Reporting | 2/2 | Complete    | 2026-08-24 |
| 5. Safe Action Engine (Dry-Run, Deletion & Unmonitoring) | 2/2 | Complete    | 2026-08-24 |
| 6. Support Composite Time Formats for Age Filters | 1/1 | Complete   | 2026-08-24 |
| 7. Scope unmonitor to episodes and add unmonitor-series option | 1/1 | Complete   | 2026-08-24 |
| 8. Support --monitored and --unmonitored filter for scan and clean | 1/1 | Complete    | 2026-08-24 |
| 9. Docker Packaging and GitHub Actions Release Workflow | 0/1 | Not started | - |

### Phase 6: Support Composite Time Formats for Age Filters

**Goal**: Support compound relative time duration strings (e.g. `1y1m1d` for 1 year, 1 month, and 1 day) in `--older-than` and `--newer-than` CLI filters
**Mode:** mvp
**Depends on**: Phase 5
**Requirements**: INVT-05
**Success Criteria** (what must be TRUE):

  1. Relative duration parser accepts compound multi-unit expressions (e.g., `1y1m1d`, `2y6m`, `18m`, `3w4d`, `2d12h`).
  2. Relative cutoffs compute exact timedelta offsets using standard year (365d) and month (30d) or calendar calculations.
  3. CLI filters `--older-than` and `--newer-than` in both `scan` and `clean` commands evaluate compound formats accurately.
  4. Invalid combinations or syntaxes produce clear, user-friendly error messages.

**Plans**: 1/1 plans complete

Plans:
**Wave 1**

- [x] 06-01-PLAN.md: Composite Time Format Parser, Test Suite & CLI Filter Integration

### Phase 7: Scope unmonitor to episodes and add unmonitor-series option

**Goal:** Ensure `--unmonitor` operates on individual media items (episodes for TV files, movies for movie files), remove `--unmonitor-episode`, and add `--unmonitor-series` for full series unmonitoring.
**Mode:** mvp
**Depends on:** Phase 5, Phase 6
**Requirements:** ACT-03, ACT-04
**Success Criteria** (what must be TRUE):

  1. `--unmonitor` flag unmonitors movies in Radarr and specific episodes in Sonarr for matched media files.
  2. `--unmonitor-episode` CLI option is completely removed.
  3. `--unmonitor-series` CLI option is added to allow unmonitoring the entire parent series in Sonarr.
  4. Action executor, confirmation panels, dry-run simulation, and execution reports reflect the new unmonitor semantics.
  5. All unit and integration test suites are updated and passing.

**Plans:** 1/1 plans complete

Plans:

- [x] 07-01-PLAN.md

### Phase 8: Support --monitored and --unmonitored filter for scan and clean

**Goal:** Enable filtering media items by monitored status across Radarr movies and Sonarr episodes in `scan` and `clean` commands (e.g., `--only-monitored` / `--monitored-only` and `--unmonitored-only`).
**Mode:** mvp
**Depends on:** Phase 7
**Requirements:** INVT-03, ACT-02
**Success Criteria** (what must be TRUE):

  1. MediaInventoryItem captures monitored status for movies in Radarr and episodes/series in Sonarr.
  2. InventoryFilter supports filtering by monitored status (e.g. `--only-monitored` or `--monitored`, and `--unmonitored`).
  3. CLI `scan` and `clean` commands expose `--monitored` / `--only-monitored` and `--unmonitored` options.
  4. Running clean with `--unmonitor --only-monitored` isolates and unmonitors currently monitored files without redundant operations.
  5. JSON reporting and table formatting reflect monitored metadata accurately.

**Plans:** 1/1 plans complete

Plans:
**Wave 1**

- [x] 08-01-PLAN.md: Monitored Status Correlation, Inventory Engine Filtering & CLI Integration

### Phase 9: Docker Packaging and GitHub Actions Release Workflow

**Goal:** Package arr-oldies into a lightweight Docker image (runnable anywhere, e.g. `docker run ghcr.io/gmcouto/arr-oldies arr-oldies --help`) and configure a GitHub Actions workflow to build and deploy the image to GHCR upon version release tags.
**Mode:** mvp
**Depends on:** Phase 8
**Requirements:** DIST-01, DIST-02
**Success Criteria** (what must be TRUE):

  1. Dockerfile builds a lightweight container with `arr-oldies` as the entrypoint supporting CLI arguments, volume mounting (e.g. `config.yaml`), and environment configuration.
  2. Users can run commands via Docker (e.g., `docker run --rm -v $(pwd)/config.yaml:/app/config.yaml ghcr.io/gmcouto/arr-oldies arr-oldies --help`).
  3. GitHub Actions workflow automates building and pushing multi-platform images (linux/amd64, linux/arm64) to `ghcr.io/gmcouto/arr-oldies` upon publishing version release tags (e.g., `v*`).
  4. README.md and documentation are updated with Docker run instructions, mounting guidelines, and CI/CD release details.

**Plans:** 0 plans

Plans:

- [ ] TBD (run /gsd-plan-phase 9 to break down)
