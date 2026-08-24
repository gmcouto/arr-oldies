# Roadmap: Arr-Oldies

## Overview

Arr-Oldies delivers a high-performance CLI tool to audit and clean stale media files across multiple Radarr and Sonarr instances. The roadmap progresses slice-by-slice in vertical MVP mode: starting from configuration and multi-instance connectivity, building robust async API clients, implementing the History API correlation engine and audio language extraction, delivering Rich CLI table reporting, and culminating in a guarded, safe action engine for file deletion, episode/show unmonitoring, and library entry removal.

## Phases

**Phase Numbering:**

- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Foundation, Multi-Instance Configuration & CLI Scaffolding** - Establish project foundation, Pydantic schemas, YAML config loading, validation command, and base CLI (completed 2026-08-23)
- [ ] **Phase 2: Async *arr API Clients & Batch History Fetcher** - Build HTTPX async clients for Radarr v3/v4 and Sonarr v3/v4 with batch history pagination and instance resilience
- [ ] **Phase 3: Media Inventory & History Timestamp Correlator** - Correlate media files with History API import/grab timestamps, extract audio languages, and build sortable/filterable inventory
- [ ] **Phase 4: Rich CLI Visualization & Reporting** - Implement Rich terminal table formatting, storage metrics summaries, output limits, and JSON export
- [ ] **Phase 5: Safe Action Engine (Dry-Run, Deletion & Unmonitoring)** - Build safe mutation pipeline with dry-run default, `--delete`, `--unmonitor`, `--unmonitor-episode`, `--remove`, and confirmation guards

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

**Plans**: TBD

Plans:

- [ ] 03-01: History correlation engine mapping event logs to movie and episode file records
- [ ] 03-02: MediaInfo audio language extractor, inventory aggregator, and sorting/filtering engine

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

- [ ] 04-01: Rich table visualizer with color-coded age tiers, units formatting, and summary cards
- [ ] 04-02: CLI scan command integration with sorting/filtering flags and JSON serialization

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

**Plans**: TBD

Plans:

- [ ] 05-01: Action executor core with dry-run simulations, batch deletion, show unmonitoring, episode unmonitoring, and entry removal
- [ ] 05-02: CLI action commands, Rich confirmation modal, and `--yes` automation bypass

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation, Multi-Instance Configuration & CLI Scaffolding | 2/2 | Complete    | 2026-08-23 |
| 2. Async *arr API Clients & Batch History Fetcher | 2/2 | In Progress|  |
| 3. Media Inventory & History Timestamp Correlator | 0/2 | Not started | - |
| 4. Rich CLI Visualization & Reporting | 0/2 | Not started | - |
| 5. Safe Action Engine (Dry-Run, Deletion & Unmonitoring) | 0/2 | Not started | - |
