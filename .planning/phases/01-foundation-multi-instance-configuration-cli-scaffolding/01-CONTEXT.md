# Phase 1: Foundation, Multi-Instance Configuration & CLI Scaffolding - Context

**Gathered:** 2026-08-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 1 establishes the core project structure, Python package scaffolding (pyproject.toml, package modules), Pydantic v2 schemas for configuration validation, YAML config loading, the `validate-config` CLI command to verify instance reachability/auth, and the base Typer CLI framework with instance targeting flags (`--radarr`, `--sonarr`, `--instance <name>`).

Out of scope for Phase 1:
- Batch history pagination and full API endpoints (Phase 2)
- Media inventory building and History timestamp correlation (Phase 3)
- Rich media scan tables and inventory queries (Phase 4)
- Safe Action Engine mutations and deletions (Phase 5)
</domain>

<decisions>
## Implementation Decisions

### Configuration Schema & Discovery
- **D-01:** Hierarchical config discovery: Explicit `--config <path>` > `./arr-oldies.yaml` / `./config.yaml` > `~/.config/arr-oldies/config.yaml`.
- **D-02:** Unified instances list: YAML structure uses a root-level `instances:` list of objects where each instance specifies `name` (unique identifier), `type` (`radarr` or `sonarr`), `url`, `api_key`, and optional connection parameters.
- **D-03:** Static YAML configuration: Deterministic, clean YAML parsing without dynamic environment variable expansion.
- **D-04:** Global defaults with per-instance overrides: Root-level `defaults:` section (e.g. `timeout: 30`, `verify_ssl: true`) applied across all instances unless overridden per instance.

### validate-config Health Probing
- **D-05:** Health check endpoint: Probe `/api/v3/system/status` with `X-Api-Key` header to verify connectivity, validate authentication, and retrieve remote instance name/version.
- **D-06:** Rich status table: Display results in a high-contrast Rich table showing Instance Name, Type, Base URL, Version, Latency (ms), and Status (green `[OK]` / red `[FAIL]` with concise error explanation).
- **D-07:** Concurrent async probing: Probe all targeted instances concurrently using `asyncio.gather` and `httpx.AsyncClient` for rapid validation.
- **D-08:** Clean diagnostic failure messages: Output user-friendly error summaries (e.g. `401 Unauthorized (Invalid API Key)` or `Connection refused at host:port`) without dumping raw Python stack traces.

### CLI Structure & Instance Targeting
- **D-09:** Default target behavior: When no instance targeting flags are specified, target all configured instances by default.
- **D-10:** Multi-instance targeting & conflicts: Allow repeatable `-i` / `--instance` flags to select multiple specific instances. Reject conflicting flags (e.g. specifying `--radarr` alongside an instance known to be Sonarr).
- **D-11:** Flexible global flags placement: Support global options (`--config`, `-v`/`--verbose`) before or after subcommands via Typer Context.
- **D-12:** Bare CLI execution: Running `arr-oldies` without subcommands renders a styled Rich help screen with version banner, subcommand descriptions, and quick usage examples.

### Error Handling & Exit Codes
- **D-13:** Exit code on validation outcome: `validate-config` exits with code 1 if ANY targeted instance fails connection/auth check; exits with code 0 only if ALL targeted instances succeed.
- **D-14:** Distinct exit codes: Exit code 2 for configuration errors (missing file, invalid YAML syntax, Pydantic schema validation failures); Exit code 1 for runtime network/instance probe failures; Exit code 0 for success.
- **D-15:** Stderr debug logging: Route verbose logs (`--verbose`) to `stderr` to keep `stdout` clean for tables and piped output.
- **D-16:** Credential masking: Mask API keys across all outputs, logs, and error messages (e.g. `abcd****` or omit) to protect credentials.

### the agent's Discretion
- Packaging and build toolchain selection (e.g., standard Hatch/Flit/Setuptools via `pyproject.toml`).
- Internal module structure within `src/arr_oldies/` (e.g. `config.py`, `models.py`, `client.py`, `cli.py`).
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project & Requirements
- `.planning/PROJECT.md` — Core value, constraints, and architecture guidelines
- `.planning/REQUIREMENTS.md` §CONF — Requirements CONF-01, CONF-02, CONF-03
- `.planning/ROADMAP.md` §Phase 1 — Phase 1 scope and deliverables

### Upstream *arr Specifications
- Radarr API v3/v4 Documentation — `/api/v3/system/status` endpoint and `X-Api-Key` header specification
- Sonarr API v3/v4 Documentation — `/api/v3/system/status` endpoint and `X-Api-Key` header specification
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- Greenfield repository: Python 3.11+ stack to be initialized with Typer, Rich, HTTPX, Pydantic v2, and PyYAML.

### Established Patterns
- Clean CLI separation: Pydantic schemas for data models, PyYAML for configuration ingestion, HTTPX for async network communication, and Typer + Rich for CLI presentation.

### Integration Points
- `arr_oldies.config`: Configuration loading, validation, and instance model resolution.
- `arr_oldies.cli`: Main Typer CLI app entrypoint and `validate-config` command.
</code_context>

<specifics>
## Specific Ideas

- Ensure `validate-config` output looks polished in terminal with clear pass/fail indicators and latency measurements in milliseconds.
- Support both YAML extensions: `.yaml` and `.yml`.
</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.
</deferred>

---

*Phase: 01-Foundation, Multi-Instance Configuration & CLI Scaffolding*
*Context gathered: 2026-08-23*
