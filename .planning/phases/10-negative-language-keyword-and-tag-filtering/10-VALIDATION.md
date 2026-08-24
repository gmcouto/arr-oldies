---
phase: 10
slug: negative-language-keyword-and-tag-filtering
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-08-24
---

# Phase 10 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest >=8.0.0, pytest-asyncio >=0.23.0, respx >=0.21.0 |
| **Config file** | pyproject.toml |
| **Quick run command** | `pytest tests/ -k "test_api_models or test_inventory or test_correlator or test_cli" -v` |
| **Full suite command** | `pytest tests/ -v` |
| **Estimated runtime** | ~2 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -v`
- **After every plan wave:** Run `pytest tests/ -v`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 10-01-01 | 01 | 1 | INVT-09 | — | N/A | unit | `pytest tests/test_api_models.py tests/test_radarr_client.py tests/test_sonarr_client.py -v` | ✅ | ⬜ pending |
| 10-01-02 | 01 | 1 | INVT-09 | — | N/A | unit | `pytest tests/test_correlator_radarr.py tests/test_correlator_sonarr.py -v` | ✅ | ⬜ pending |
| 10-02-01 | 02 | 2 | INVT-07, INVT-08, INVT-09 | — | Safe input sanitization / lowercasing | unit | `pytest tests/test_inventory_engine.py -v` | ✅ | ⬜ pending |
| 10-02-02 | 02 | 2 | INVT-07, INVT-08, INVT-09 | — | Dry-run safety and filter consistency | integration | `pytest tests/test_cli_scan.py tests/test_cli_clean.py -v` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements.

---

## Manual-Only Verifications

All phase behaviors have automated verification.

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
