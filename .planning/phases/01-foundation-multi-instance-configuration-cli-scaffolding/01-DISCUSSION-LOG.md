# Phase 1: Foundation, Multi-Instance Configuration & CLI Scaffolding - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-08-23
**Phase:** 1-Foundation, Multi-Instance Configuration & CLI Scaffolding
**Areas discussed:** Configuration Schema & Discovery, validate-config Health Probing, CLI Structure & Instance Targeting, Error Handling & Exit Codes

---

## Configuration Schema & Discovery

| Option | Description | Selected |
|--------|-------------|----------|
| Hierarchical lookup | Explicit `--config` > `./arr-oldies.yaml` / `./config.yaml` > `~/.config/arr-oldies/config.yaml` | ✓ |
| Fixed local path | Only look for `./config.yaml` in working directory unless `--config` is passed | |
| You decide | Agent discretion | |

**User's choice:** Hierarchical lookup: explicit --config > ./arr-oldies.yaml / ./config.yaml > ~/.config/arr-oldies/config.yaml

| Option | Description | Selected |
|--------|-------------|----------|
| Unified instances list | `instances: [{name: "radarr-main", type: "radarr", url: "...", api_key: "..."}, ...]` | ✓ |
| Top-level service sections | `radarr: [{...}], sonarr: [{...}]` | |
| You decide | Agent discretion | |

**User's choice:** Unified instances list with explicit type

| Option | Description | Selected |
|--------|-------------|----------|
| Env var syntax expansion | Support `${ENV_VAR}` syntax expansion in YAML + `ARR_OLDIES_CONFIG` | |
| Static YAML only | Simple, deterministic, no environment variable expansion | ✓ |
| You decide | Agent discretion | |

**User's choice:** Static YAML only

| Option | Description | Selected |
|--------|-------------|----------|
| Global defaults with overrides | Root-level settings (`timeout: 30`, `verify_ssl: true`) with per-instance override capability | ✓ |
| Per-instance only | Instances define timeout/ssl directly if non-default, no top-level defaults block | |
| You decide | Agent discretion | |

**User's choice:** Global defaults section with per-instance overrides

---

## validate-config Health Probing

| Option | Description | Selected |
|--------|-------------|----------|
| `/api/v3/system/status` | Lightweight standard endpoint; returns instance version, appName, and status while verifying API key | ✓ |
| `/api/v3/health` | Health check endpoint checking health flags | |
| You decide | Agent discretion | |

**User's choice:** `/api/v3/system/status`

| Option | Description | Selected |
|--------|-------------|----------|
| Rich status table | Displays Instance Name, Type, Base URL, Version, Latency (ms), and Status ([OK] / [FAIL]) | ✓ |
| Minimalist text lines | Simple streaming [OK] / [FAIL] output as each instance is checked | |
| You decide | Agent discretion | |

**User's choice:** Rich status table

| Option | Description | Selected |
|--------|-------------|----------|
| Concurrent async probes | Probe all targeted instances simultaneously with `asyncio.gather` | ✓ |
| Sequential probing | Probe instances one by one | |
| You decide | Agent discretion | |

**User's choice:** Concurrent async probes

| Option | Description | Selected |
|--------|-------------|----------|
| Clean diagnostic message | Summarize exact HTTP status / network error without dumping raw Python stack traces | ✓ |
| Full debug stack traces | Print full debug tracebacks on error by default | |
| You decide | Agent discretion | |

**User's choice:** Clean diagnostic message

---

## CLI Structure & Instance Targeting

| Option | Description | Selected |
|--------|-------------|----------|
| Target all configured instances by default | Validates or scans everything defined in config unless narrowed down | ✓ |
| Require explicit target | Fail or prompt if no instance/type flag is specified | |
| You decide | Agent discretion | |

**User's choice:** Target all configured instances by default

| Option | Description | Selected |
|--------|-------------|----------|
| Repeatable `-i`/`--instance` flags + exclusive filters | Support repeatable `--instance` flags, error on conflicting filters | ✓ |
| Single `--instance` with strict precedence | Single instance flag only | |
| You decide | Agent discretion | |

**User's choice:** Repeatable `--instance` flags + mutually exclusive service filters

| Option | Description | Selected |
|--------|-------------|----------|
| Flexible placement via Typer Context | Allow global flags before or after subcommands seamlessly | ✓ |
| Subcommand-only placement | Flags must strictly appear after subcommand name | |
| You decide | Agent discretion | |

**User's choice:** Flexible placement via Typer Context

| Option | Description | Selected |
|--------|-------------|----------|
| Rich help and usage overview | Display version banner, available subcommands, and quickstart examples | ✓ |
| Run scan automatically | Execute default audit scan when no subcommand is provided | |
| You decide | Agent discretion | |

**User's choice:** Rich help and usage overview

---

## Error Handling & Exit Codes

| Option | Description | Selected |
|--------|-------------|----------|
| Exit code 1 if ANY fails | Exit 1 if any targeted instance fails validation; exit 0 only if all pass | ✓ |
| Exit code 0 on partial success | Exit 0 if at least one instance succeeds (with warning) | |
| You decide | Agent discretion | |

**User's choice:** Exit code 1 if ANY targeted instance fails validation; exit 0 only if ALL pass

| Option | Description | Selected |
|--------|-------------|----------|
| Distinct exit codes | Exit 2 for config errors, Exit 1 for network/instance errors, Exit 0 for success | ✓ |
| Uniform Exit 1 | Exit 1 for any error | |
| You decide | Agent discretion | |

**User's choice:** Distinct exit codes (Exit 2 for config errors, Exit 1 for network/instance errors, Exit 0 for success)

| Option | Description | Selected |
|--------|-------------|----------|
| Stderr debug logging | Route `--verbose` logs to stderr so stdout remains clean for tables and piped JSON | ✓ |
| Stdout debug logging | Print debug messages directly to stdout | |
| You decide | Agent discretion | |

**User's choice:** Stderr debug logging

| Option | Description | Selected |
|--------|-------------|----------|
| Masked API keys across all outputs | Never print full API keys in tables, logs, or error messages | ✓ |
| Print full API keys when `--verbose` is passed | Show credentials in verbose mode | |
| You decide | Agent discretion | |

**User's choice:** Masked API keys across all outputs

---

## the agent's Discretion

- Packaging and build toolchain selection in `pyproject.toml`.
- Internal module layout within `src/arr_oldies/`.

## Deferred Ideas

None — discussion stayed within phase scope.
