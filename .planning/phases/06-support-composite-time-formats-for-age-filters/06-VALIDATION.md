---
phase: 6
slug: support-composite-time-formats-for-age-filters
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-08-24
---

# Phase 6 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.1.1 + pytest-asyncio 1.4.0 + respx 0.23.1 |
| **Config file** | `pyproject.toml` (`[tool.pytest.ini_options] asyncio_mode = "auto"`) |
| **Quick run command** | `.venv/bin/pytest tests/test_parser.py tests/test_cli_scan.py tests/test_cli_clean.py -q` |
| **Full suite command** | `.venv/bin/pytest` |
| **Estimated runtime** | ~3 seconds |

---

## Sampling Rate

- **After every task commit:** Run `.venv/bin/pytest tests/test_parser.py -q`
- **After every plan wave:** Run `.venv/bin/pytest`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 06-01-01 | 01 | 1 | INVT-05 | T-06-01 | Composite time format regex tokenization and parsing in parse_age_cutoff | unit | `.venv/bin/pytest tests/test_parser.py` | ✅ Yes | ⬜ pending |
| 06-01-02 | 01 | 1 | INVT-05 | T-06-02 | CLI scan and clean integration testing with composite age filter arguments | integration | `.venv/bin/pytest tests/test_cli_scan.py tests/test_cli_clean.py` | ✅ Yes | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing test files already exist and will be extended with new composite duration test cases:
- [x] `tests/test_parser.py` — unit tests for parse_age_cutoff
- [x] `tests/test_cli_scan.py` — integration tests for scan command
- [x] `tests/test_cli_clean.py` — integration tests for clean command

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 5s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-08-24
