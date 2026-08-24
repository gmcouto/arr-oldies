---
phase: 4
slug: rich-cli-visualization-reporting
status: approved
nyquist_compliant: true
wave_0_complete: false
created: 2026-08-24
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.1.1, pytest-asyncio 1.4.0, respx 0.23.1 |
| **Config file** | `pyproject.toml` (`[tool.pytest.ini_options] asyncio_mode = "auto"`) |
| **Quick run command** | `.venv/bin/pytest tests/test_reporting*.py tests/test_formatters.py -q` |
| **Full suite command** | `.venv/bin/pytest` |
| **Estimated runtime** | ~2 seconds |

---

## Sampling Rate

- **After every task commit:** Run `.venv/bin/pytest tests/test_reporting*.py tests/test_formatters.py tests/test_cli_scan.py -q`
- **After every plan wave:** Run `.venv/bin/pytest`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 04-01-01 | 01 | 1 | CLI-01 | — | Format IEC binary sizes and human ages | unit | `.venv/bin/pytest tests/test_formatters.py` | ❌ W0 | ⬜ pending |
| 04-01-02 | 01 | 1 | CLI-01 | T-04-02 | Escape terminal strings and format Rich table | unit | `.venv/bin/pytest tests/test_reporting_table.py` | ❌ W0 | ⬜ pending |
| 04-01-03 | 01 | 1 | CLI-02 | — | Render summary metrics panel with storage stats | unit | `.venv/bin/pytest tests/test_reporting_summary.py` | ❌ W0 | ⬜ pending |
| 04-02-01 | 02 | 2 | CLI-04 | T-04-01 | Clean JSON export without ANSI escapes | unit | `.venv/bin/pytest tests/test_reporting_json.py` | ❌ W0 | ⬜ pending |
| 04-02-02 | 02 | 2 | CLI-01, CLI-02, CLI-03, CLI-04 | T-04-01 | CLI scan command with limit, sorting, filters, and formats | integration | `.venv/bin/pytest tests/test_cli_scan.py` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_formatters.py` — unit tests for size, age, badge, and title formatters
- [ ] `tests/test_reporting_table.py` — unit tests for Rich table rendering and styling
- [ ] `tests/test_reporting_summary.py` — unit tests for storage and date range summary card
- [ ] `tests/test_reporting_json.py` — unit tests for JSON export model and serializer
- [ ] `tests/test_cli_scan.py` — CLI integration tests for `arr-oldies scan` command

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| High-contrast terminal rendering check | CLI-01 | Terminal visual aesthetics | Run `arr-oldies scan` in a true terminal window and visually confirm colors and alignment |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 5s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-08-24

