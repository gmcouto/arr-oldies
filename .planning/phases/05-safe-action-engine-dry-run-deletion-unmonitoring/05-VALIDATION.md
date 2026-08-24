---
phase: 5
slug: safe-action-engine-dry-run-deletion-unmonitoring
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-08-24
---

# Phase 5 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.1.1 + pytest-asyncio 1.4.0 + respx 0.23.1 |
| **Config file** | `pyproject.toml` (`[tool.pytest.ini_options] asyncio_mode = "auto"`) |
| **Quick run command** | `.venv/bin/pytest tests/test_action*.py tests/test_cli_clean.py -q` |
| **Full suite command** | `.venv/bin/pytest` |
| **Estimated runtime** | ~3 seconds |

---

## Sampling Rate

- **After every task commit:** Run `.venv/bin/pytest tests/test_action*.py tests/test_*client_actions.py tests/test_cli_clean.py -q`
- **After every plan wave:** Run `.venv/bin/pytest`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 05-01-01 | 01 | 1 | ACT-01, ACT-02, ACT-03, ACT-04, ACT-05 | T-05-01 | Define immutable action models and mutation payload schemas | unit | `.venv/bin/pytest tests/test_action_models.py` | ❌ W0 | ⬜ pending |
| 05-01-02 | 01 | 1 | ACT-02, ACT-03, ACT-05 | T-05-04 | Extend RadarrClient with file delete, movie unmonitor, and entry removal | unit | `.venv/bin/pytest tests/test_radarr_client_actions.py` | ❌ W0 | ⬜ pending |
| 05-01-03 | 01 | 1 | ACT-02, ACT-03, ACT-04, ACT-05 | T-05-04 | Extend SonarrClient with file delete, series/episode unmonitor, and series removal | unit | `.venv/bin/pytest tests/test_sonarr_client_actions.py` | ❌ W0 | ⬜ pending |
| 05-01-04 | 01 | 1 | ACT-01, ACT-02, ACT-03, ACT-04, ACT-05 | T-05-03 | ActionExecutor dry-run plan generator and ordered execution engine | unit | `.venv/bin/pytest tests/test_action_executor.py` | ❌ W0 | ⬜ pending |
| 05-02-01 | 02 | 2 | ACT-06, ACT-07 | T-05-01, T-05-02 | Rich confirmation modal and interactive prompt guard | unit | `.venv/bin/pytest tests/test_confirmation.py` | ❌ W0 | ⬜ pending |
| 05-02-02 | 02 | 2 | ACT-01, ACT-02, ACT-03, ACT-04, ACT-05, ACT-06, ACT-07 | T-05-01, T-05-02 | CLI clean command with filters, execution safety guards, and output formatting | integration | `.venv/bin/pytest tests/test_cli_clean.py` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_action_models.py` — unit tests for action types, plans, items, and reports
- [ ] `tests/test_radarr_client_actions.py` — unit tests for Radarr mutation endpoints
- [ ] `tests/test_sonarr_client_actions.py` — unit tests for Sonarr mutation endpoints
- [ ] `tests/test_action_executor.py` — unit tests for ActionExecutor planning and execution pipeline
- [ ] `tests/test_confirmation.py` — unit tests for Rich confirmation panel and prompt guards
- [ ] `tests/test_cli_clean.py` — integration tests for CLI `clean` command

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| High-contrast safety warning panel aesthetic check | ACT-06 | Visual styling verification | Run `arr-oldies clean --delete --execute` against a test instance to visually inspect red banner and prompt |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 5s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-08-24
