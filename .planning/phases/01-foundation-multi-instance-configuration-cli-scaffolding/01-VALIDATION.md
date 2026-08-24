---
phase: 01
slug: foundation-multi-instance-configuration-cli-scaffolding
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-08-23
---

# Phase 01 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest >=8.0.0, pytest-asyncio >=0.23.0, respx >=0.21.0 |
| **Config file** | `pyproject.toml` (pytest configuration) |
| **Quick run command** | `pytest tests/test_models.py tests/test_config.py -x` |
| **Full suite command** | `pytest tests/` |
| **Estimated runtime** | ~2-5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/`
- **After every plan wave:** Run `pytest tests/`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | CONF-01 | T-01-01 | `SecretStr` prevents API key leakage in string representation | unit | `pytest tests/test_models.py -k test_secret_masking` | ❌ W0 | ⬜ pending |
| 01-01-02 | 01 | 1 | CONF-01 | T-01-03 | Safe YAML loading with `yaml.safe_load` | unit | `pytest tests/test_config.py -k test_yaml_safe_load` | ❌ W0 | ⬜ pending |
| 01-01-03 | 01 | 1 | CONF-01 | — | Hierarchy discovery and defaults merging | unit | `pytest tests/test_config.py` | ❌ W0 | ⬜ pending |
| 01-02-01 | 02 | 2 | CONF-03 | — | Instance filtering and conflict detection | unit | `pytest tests/test_targeting.py` | ❌ W0 | ⬜ pending |
| 01-02-02 | 02 | 2 | CONF-02 | T-01-01 | Async HTTPX status probe with credential masking | unit | `pytest tests/test_prober.py` | ❌ W0 | ⬜ pending |
| 01-02-03 | 02 | 2 | CONF-02, CONF-03 | — | Typer CLI commands, exit codes (0/1/2), Rich tables | integration | `pytest tests/test_cli.py` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/conftest.py` — shared fixtures and sample YAML configs
- [ ] `tests/test_models.py` — Pydantic schema validation tests
- [ ] `tests/test_config.py` — configuration discovery and loader tests
- [ ] `tests/test_targeting.py` — instance resolution and conflict handling tests
- [ ] `tests/test_prober.py` — async HTTPX status prober tests with respx
- [ ] `tests/test_cli.py` — Typer CLI runner and exit code integration tests

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Rich Table Visual Polish | CONF-02 | Visual formatting / colors in terminal | Run `arr-oldies validate-config` and inspect terminal colors, column alignment, and status symbols |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
