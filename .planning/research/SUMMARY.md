# Project Research Summary

**Project:** Arr-Oldies
**Domain:** Media Server Management & *arr Automation CLI
**Researched:** 2026-08-23
**Confidence:** HIGH

## Executive Summary

Arr-Oldies is a high-performance Python CLI tool designed to solve media server storage sprawl across multi-instance Radarr and Sonarr environments. By connecting directly to Radarr (v3/v4) and Sonarr (v3/v4) REST APIs, the tool queries `/api/v3/history` to establish definitive download and import event timestamps for every media file. This allows users to view an actionable, sorted list of the oldest files on their systems, calculate storage impact, and safely perform cleanup operations.

The recommended architectural approach utilizes an asynchronous client stack (HTTPX + asyncio) paired with Typer and Rich. This ensures fast concurrent scanning across multiple local or remote instances with beautiful, high-contrast terminal tables. Safety is paramount: all operations default to dry-run simulations, requiring explicit flags (`--execute` and `--yes`) and interactive confirmations for deletions and unmonitoring.

Key risks include SQLite database lock contention in *arr apps during massive history pagination and missing history events on legacy imports. These risks are mitigated through optimized batch pagination (500–1000 items/page), rate-limited concurrency, and explicit handling for unindexed files.

## Key Findings

### Recommended Stack

- **Core:** Python 3.11+, Typer (CLI routing), Rich (terminal tables, progress & styling), HTTPX (async client), Pydantic v2 (data modeling & validation), PyYAML (config parsing).
- **Testing:** pytest, pytest-asyncio, respx (mocking HTTPX requests to Radarr/Sonarr).

### Expected Features

- **Table Stakes:** Multi-instance YAML config, concurrent API polling, deep History API timestamp matching (`downloadFolderImported` / `grabbed`), oldest-first sorting, rich tabular terminal output, default dry-run safety.
- **Differentiators:** Safe batch deletion with automatic unmonitoring (`--unmonitor`), summary storage analytics by age brackets, structured JSON/CSV exports.
- **Anti-Features:** Direct OS file deletions (causes database desync), unattended daemon services (risks accidental data loss).

### Architecture Approach

Separated into 4 primary layers:
1. **CLI Layer:** Typer commands, arguments, flag parsing, Rich formatting.
2. **Core Engine:** History correlator, inventory aggregator, filtering/sorting, safe action executor.
3. **Client Layer:** Async Radarr and Sonarr API clients with connection pooling and pagination helpers.
4. **Configuration & Models:** Pydantic schemas for instance configs and unified media items.

### Critical Pitfalls

1. **Re-download loops:** Deleting files without unmonitoring them triggers automatic re-grabs. Mitigate with integrated unmonitor capabilities.
2. **History pagination performance:** Small page sizes cause slow scans and database locks. Mitigate with large page size (500-1000) and concurrent batching.
3. **Missing history logs:** Legacy imports may lack history events. Mitigate by cleanly flagging unindexed items without crashing.
4. **Accidental data loss:** Mitigate with strict dry-run defaults, explicit `--execute`, and interactive confirmation prompts.

## Implications for Roadmap

Suggested phase structure:

### Phase 1: Core Foundation & Multi-Instance Configuration
- **Rationale:** Establishes project structure, Pydantic schemas, YAML/JSON configuration loading, and CLI scaffolding.
- **Delivers:** Configuration parser, validation tests, base CLI commands (`version`, `validate-config`).

### Phase 2: Async *arr API Clients & History Retrieval Engine
- **Rationale:** Builds robust async clients for Radarr (v3/v4) and Sonarr (v3/v4), implementing optimized history pagination and error handling.
- **Delivers:** `RadarrClient`, `SonarrClient`, batch history fetcher, mock fixtures for testing.
- **Avoids:** Unreachable instance crashes and inefficient API pagination.

### Phase 3: Media Inventory & History Timestamp Correlator
- **Rationale:** Connects media files with History API events (`downloadFolderImported`, `grabbed`) and builds the unified sortable inventory.
- **Delivers:** Correlation engine, missing-history handler, multi-instance aggregator, sorting (oldest first) and filtering (instance, type, size, age).

### Phase 4: Rich CLI Reporting & Table Visualization
- **Rationale:** Delivers the primary user interface for inspecting oldest media files in the terminal.
- **Delivers:** Rich table formatter, summary stats (total size, age breakdown), CLI flags (`--limit`, `--by`, `--instance`, `--type`), and JSON export.

### Phase 5: Safe Action Engine (Dry-Run, Deletion & Unmonitoring)
- **Rationale:** Implements the write actions with robust safeguards.
- **Delivers:** Dry-run execution simulation, `--execute` mode with interactive confirmation prompts, `--yes` flag for automation, API-driven deletion and unmonitoring.
- **Avoids:** Accidental file loss and re-download loops.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Python + Typer + Rich + HTTPX is battle-tested for *arr automation tools |
| Features | HIGH | Explicit user requirements and standard *arr workflow alignment |
| Architecture | HIGH | Clean decoupled layered design |
| Pitfalls | HIGH | History API nuances and unmonitor behaviors thoroughly verified |

**Overall confidence:** HIGH

---
*Research completed: 2026-08-23*
*Ready for roadmap: yes*
