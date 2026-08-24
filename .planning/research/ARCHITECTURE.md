# Architecture Research

**Domain:** Media Server Management & *arr Automation CLI
**Researched:** 2026-08-23
**Confidence:** HIGH

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      CLI Layer (Typer + Rich)                   │
├─────────────────────────────────────────────────────────────────┤
│  ┌────────────────┐  ┌──────────────────┐  ┌─────────────────┐  │
│  │ Scan / List    │  │ Action (Delete)  │  │ Config Validate │  │
│  └───────┬────────┘  └────────┬─────────┘  └────────┬────────┘  │
│          │                    │                     │           │
├──────────┴────────────────────┴─────────────────────┴───────────┤
│                       Core Service & Engine                     │
├─────────────────────────────────────────────────────────────────┤
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    Media Inventory Engine                 │  │
│  │   (Aggregates files, sorts by date, applies filters)      │  │
│  └────────────────────────────┬──────────────────────────────┘  │
│                               │                                 │
│  ┌────────────────────────────┴──────────────────────────────┐  │
│  │                 History Correlation Engine                │  │
│  │ (Maps downloadFolderImported & grabbed events to file IDs)│  │
│  └────────────────────────────┬──────────────────────────────┘  │
├───────────────────────────────┴─────────────────────────────────┤
│                       API & Client Layer                        │
│  ┌───────────────────────────┐     ┌─────────────────────────┐  │
│  │   RadarrClient (Async)    │     │   SonarrClient (Async)  │  │
│  └─────────────┬─────────────┘     └────────────┬────────────┘  │
└────────────────┼────────────────────────────────┼───────────────┘
                 ▼                                ▼
       [Radarr Instances]                [Sonarr Instances]
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| `cli` (`arr_oldies.cli`) | Entry points, flag parsing, command dispatch, Rich table rendering, interactive confirmation prompts | Typer application with Rich console |
| `config` (`arr_oldies.config`) | Loads, validates YAML/JSON config file with Pydantic models for instance definitions | Pydantic BaseSettings / BaseModel + PyYAML |
| `clients` (`arr_oldies.clients`) | Async HTTP clients for Radarr and Sonarr REST APIs (fetching movies, series, files, history, deletion, unmonitoring) | `httpx.AsyncClient` with authentication headers, retry policies, pagination helpers |
| `correlator` (`arr_oldies.correlator`) | Maps raw `/api/v3/history` records to active media files to accurately deduce import and download timestamps | Pure domain logic / dictionary indexing |
| `inventory` (`arr_oldies.inventory`) | In-memory unified inventory model representing media items, sizes, instances, ages, and sorting/filtering criteria | Pydantic models with filtering and sorting methods |
| `actions` (`arr_oldies.actions`) | Safe execution pipeline: dry-run evaluation, confirmation prompts, batch API deletion and unmonitoring | Command pattern with rollback awareness and structured result logging |

## Recommended Project Structure

```
arr_oldies/
├── __init__.py
├── __main__.py
├── cli.py                  # CLI commands (scan, delete, unmonitor, version)
├── config.py               # Config loading and Pydantic schemas
├── models.py               # Unified data structures (MediaItem, HistoryEvent, InstanceConfig)
├── clients/
│   ├── __init__.py
│   ├── base.py             # Base HTTPX client with retries and auth
│   ├── radarr.py           # Radarr v3/v4 client
│   └── sonarr.py           # Sonarr v3/v4 client
├── engine/
│   ├── __init__.py
│   ├── correlator.py       # History-to-file timestamp matching engine
│   ├── inventory.py        # Multi-instance scanner & aggregator
│   └── actions.py          # Safe action executor (dry-run, delete, unmonitor)
└── formatters/
    ├── __init__.py
    ├── table.py            # Rich tables and summary display
    └── export.py           # JSON/CSV exporter
tests/
├── conftest.py             # Fixtures for mocked Radarr/Sonarr responses
├── test_config.py          # Config validation tests
├── test_clients.py         # Radarr & Sonarr client unit tests (respx)
├── test_correlator.py      # History timestamp matching tests
├── test_inventory.py       # Sorting & filtering tests
├── test_actions.py          # Dry-run vs execute action tests
└── test_cli.py             # CLI command end-to-end tests
pyproject.toml
README.md
```

### Structure Rationale

- **`clients/` separation:** Radarr and Sonarr have distinct endpoint shapes (`/api/v3/movie` vs `/api/v3/series` + `/api/v3/episodefile`). Isolating clients ensures clean API decoupling.
- **`engine/correlator.py`:** Separates network fetching from the algorithmic complexity of matching history event logs with file IDs.
- **`engine/actions.py`:** Enforces safety guarantees centrally so all delete/unmonitor operations pass through uniform dry-run and confirmation checks.

## Architectural Patterns

### Pattern 1: Async Concurrent Instance Fan-Out

**What:** Query all configured Radarr and Sonarr instances concurrently using `asyncio.gather` while respecting per-instance connection limits.
**When to use:** Multi-instance scanning where instances may be on different local or remote networks.
**Trade-offs:** Drastically improves CLI response time; requires clean error handling so one unreachable instance doesn't fail the entire scan.

### Pattern 2: Dry-Run Guard Pattern

**What:** The core action executor defaults to a simulated execution plan. Deletions and mutations are only executed if an explicit execution token is confirmed.
**When to use:** Any destructive CLI tool dealing with user storage.
**Trade-offs:** Adds a layer of indirection, but guarantees zero accidental data loss.

## Data Flow

### Scan and Audit Flow

```
[CLI 'scan' command]
    ↓ (reads config)
[Config Loader] ──> [List of Instances]
    ↓ (concurrent queries via HTTPX)
[RadarrClient / SonarrClient] ──> [Fetch Media Files + Fetch History Records]
    ↓ (raw records)
[History Correlator] ──> [Resolve exact Import/Download Timestamp per file]
    ↓ (unified items)
[Inventory Index] ──> [Filter (type, instance, age, size) & Sort (oldest first)]
    ↓
[Rich Table Formatter] ──> [Render Terminal Output]
```

### Action (Delete / Unmonitor) Flow

```
[CLI 'clean' or '--execute' command]
    ↓
[Inventory Index] ──> [Select Target Items]
    ↓
[Action Executor] ──> If not --execute: Print Dry-Run Summary & EXIT
                  ──> If --execute and not --yes: Prompt "Are you sure you want to delete N files (X GB)?"
                  ──> If confirmed: Call DELETE /api/v3/{moviefile|episodefile}/{id}
                  ──> If unmonitor enabled: Call PUT /api/v3/{movie|series} (monitored: false)
    ↓
[Action Summary] ──> [Render Execution Report (Success/Failures)]
```

---
*Architecture research for: Media Server Management & *arr Automation CLI*
*Researched: 2026-08-23*
