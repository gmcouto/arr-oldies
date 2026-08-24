---
phase: 8
slug: support-monitored-and-unmonitored-filter-for-scan-and-clean
status: validated
nyquist_compliant: true
wave_0_complete: true
created: 2026-08-24
---

# Phase 8 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.1.1 (pytest-asyncio, respx) |
| **Config file** | pyproject.toml |
| **Quick run command** | `.venv/bin/pytest tests/test_inventory_engine.py tests/test_cli_scan.py tests/test_cli_clean.py -v` |
| **Full suite command** | `.venv/bin/pytest` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `.venv/bin/pytest tests/test_inventory_engine.py tests/test_cli_scan.py tests/test_cli_clean.py`
- **After every plan wave:** Run `.venv/bin/pytest`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 08-01-01 | 01 | 1 | INVT-03 | — | N/A | unit | `.venv/bin/pytest tests/test_inventory_models.py tests/test_correlator_radarr.py tests/test_correlator_sonarr.py tests/test_inventory_engine.py` | ✅ | ⬜ pending |
| 08-01-02 | 01 | 1 | ACT-02 | — | N/A | integration | `.venv/bin/pytest tests/test_cli_scan.py tests/test_cli_clean.py` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements.

---

## Manual-Only Verifications

All phase behaviors have automated verification.

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 10s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved
