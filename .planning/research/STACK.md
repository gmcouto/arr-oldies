# Stack Research

**Domain:** Media Server Management & *arr Automation CLI
**Researched:** 2026-08-23
**Confidence:** HIGH

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

```bash
# Core & Supporting
pip install "typer[all]>=0.12.0" "rich>=13.7.0" "httpx>=0.27.0" "pydantic>=2.7.0" "pyyaml>=6.0.1"

# Dev dependencies
pip install -e ".[dev]" # includes pytest, pytest-asyncio, respx, ruff, mypy
```

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

**If running in automated / headless environment (cron/scripts):**
- Use `--execute --yes --format json` (or rich plain formatting)
- Avoid interactive prompts; parse JSON or stream standard exit codes

**If running interactively in terminal:**
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

---
*Stack research for: Media Server Management & *arr Automation CLI*
*Researched: 2026-08-23*
