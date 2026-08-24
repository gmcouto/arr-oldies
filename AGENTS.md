<!-- GSD:project-start source:PROJECT.md -->

## Project

**Arr-Oldies**

Arr-Oldies is a CLI tool and auditing engine that connects to multiple Radarr and Sonarr instances to inventory all downloaded media files, correlate them with precise download and import event timestamps from the *arr History API, and list media files sorted by oldest downloads/imports. It allows self-hosters and media server administrators to inspect media age distribution, filter by audio language and explicit instance types, and safely execute targeted actions (deleting files, unmonitoring shows or individual episodes, or removing full library entries) with robust dry-run defaults.

**Core Value:** Accurately inventory and trace media files across multiple Radarr and Sonarr instances back to their exact History API download/import timestamps, presenting an actionable, sortable audit with audio language filtering and safe, granular execution controls.

### Constraints

- **Tech stack**: Python 3.11+ (Rich, Typer, HTTPX, Pydantic v2, PyYAML)
- **Safety**: Dry-run by default; explicit `--execute` required for any mutation; confirmation prompt required unless `--yes` is specified.
- **API Compatibility**: Must support standard Radarr v3/v4 and Sonarr v3/v4 REST APIs.
- **History Requirement**: Strictly require History API events to resolve download/import timestamps.

<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->

## Technology Stack

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | 3.11+ | Core language | High productivity, modern async support, rich ecosystem for CLI tools and REST APIs |
| Typer | >=0.12.0 | CLI framework & command parsing | Type-hint driven, intuitive subcommand routing, automatic help generation, seamless Rich integration |
| Rich | >=13.7.0 | Terminal formatting & tables | Industry standard for Python terminal UI, progress bars, tables with sorting/coloring, and interactive prompts |
| HTTPX | >=0.27.0 | Async HTTP client | Fully async/await native, connection pooling, timeout handling, clean client interface for querying multiple *arr instances concurrently |
| Pydantic | >=2.7.0 | Data modeling & schema validation | Strict validation of YAML/JSON configuration files, *arr API responses, and serialized output models |
| PyYAML | >=6.0.1 | Configuration file parsing | Standard YAML parser for multi-instance configuration files |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | >=8.0.0 | Unit and integration testing | Comprehensive test suite including mocked *arr API fixtures |
| pytest-asyncio | >=0.23.0 | Async test runner | Testing async HTTP client requests and concurrent polling |
| respx | >=0.21.0 | HTTPX mocking | Deterministic mocking of Radarr and Sonarr API responses |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| ruff | Fast linter and code formatter | Configured via pyproject.toml |
| mypy | Static type checking | Strict type validation for models and client APIs |
| pip / uv | Fast package management | Modern Python dependency management |

## Installation

# Core & Supporting

# Dev dependencies

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| Typer + Rich | Click + tabulate | If minimizing dependencies, though Rich provides far superior styling and table capabilities |
| HTTPX | requests / aiohttp | `requests` is sync-only (slow when polling multiple instances/pages); `aiohttp` has a heavier API surface |
| Pydantic v2 | dataclasses + marshmallow | When zero external dependencies are required, but Pydantic v2 offers unmatched validation speed |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| Synchronous requests in loops | Serial HTTP requests across multiple instances and paginated history create intolerable CLI latency | Async `httpx.AsyncClient` with `asyncio.gather` |
| Direct filesystem scanning / deletion | Direct filesystem operations cause desync with Radarr/Sonarr internal databases and file tracking | Official Radarr/Sonarr v3/v4 REST APIs |
| Custom ad-hoc JSON parsing | Fragile with breaking changes across Radarr/Sonarr minor versions | Pydantic model validation with optional/extra field tolerance |

## Stack Patterns by Variant

- Use `--execute --yes --format json` (or rich plain formatting)
- Avoid interactive prompts; parse JSON or stream standard exit codes
- Use Rich interactive progress bars while fetching history from multiple instances
- Render colored tables with size, age, instance tags, and clear confirmation modals

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| Radarr API v3 / v4 | HTTPX >=0.27.0 | Standard header `X-Api-Key: <key>` |
| Sonarr API v3 / v4 | HTTPX >=0.27.0 | Standard header `X-Api-Key: <key>` |
| Pydantic v2 | Typer >=0.12.0 | Full support for Pydantic types in CLI arguments |

## Sources

- Radarr API v3/v4 Documentation & GitHub Specifications
- Sonarr API v3/v4 Documentation & History endpoints
- Official Python / Typer / HTTPX / Rich Documentation

<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->

## Conventions

### Documentation Maintenance
- **Keep README.md Synchronized**: Whenever adding, modifying, or removing CLI commands, flags/options, configuration settings, or core application workflows, ensure `README.md` is kept up to date to reflect the latest syntax, features, and examples.

<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->

## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->

## Project Skills

No project skills found. Add skills to any of: `.agents/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->

## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:

- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:profile-start -->

## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
