---
phase: 3
slug: media-inventory-history-timestamp-correlator
status: ready
nyquist_compliant: true
wave_0_complete: false
created: 2026-08-23
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.1.1, pytest-asyncio 1.4.0 |
| **Config file** | pyproject.toml |
| **Quick run command** | `.venv/bin/pytest tests/test_inventory*.py tests/test_correlator*.py tests/test_language*.py tests/test_parser*.py -q` |
| **Full suite command** | `.venv/bin/pytest` |
| **Estimated runtime** | ~1 second |

---

## Sampling Rate

- **After every task commit:** Run `.venv/bin/pytest tests/test_inventory*.py tests/test_correlator*.py -q`
- **After every plan wave:** Run `.venv/bin/pytest`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 1 | INVT-02 | — | Normalizes language codes & names safely | unit | `.venv/bin/pytest tests/test_language_normalizer.py` | ❌ W0 | ⬜ pending |
| 03-01-02 | 01 | 1 | INVT-05 | T-03-01 | Input validation for size and age cutoff strings | unit | `.venv/bin/pytest tests/test_parser.py` | ❌ W0 | ⬜ pending |
| 03-01-03 | 01 | 1 | INVT-03 | — | Unified media record creation and age calculation | unit | `.venv/bin/pytest tests/test_inventory_models.py` | ❌ W0 | ⬜ pending |
| 03-02-01 | 02 | 2 | INVT-01 | T-03-02 | In-memory hash index bounds check and memory safety | unit | `.venv/bin/pytest tests/test_correlator_radarr.py` | ❌ W0 | ⬜ pending |
| 03-02-02 | 02 | 2 | INVT-01 | — | Sonarr episode file & multi-episode history correlation | unit | `.venv/bin/pytest tests/test_correlator_sonarr.py` | ❌ W0 | ⬜ pending |
| 03-02-03 | 02 | 2 | INVT-06 | — | Clean fallback to date_added for legacy media | unit | `.venv/bin/pytest tests/test_correlator_legacy.py` | ❌ W0 | ⬜ pending |
| 03-02-04 | 02 | 2 | INVT-04, INVT-05 | — | Multi-dimensional filtering and oldest-first sorting | unit | `.venv/bin/pytest tests/test_inventory_engine.py` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_language_normalizer.py` — covers INVT-02
- [ ] `tests/test_parser.py` — covers human-friendly size and age string parsing
- [ ] `tests/test_inventory_models.py` — covers INVT-03
- [ ] `tests/test_correlator_radarr.py` — covers INVT-01 (Radarr movie file correlation)
- [ ] `tests/test_correlator_sonarr.py` — covers INVT-01 (Sonarr episode file correlation)
- [ ] `tests/test_correlator_legacy.py` — covers INVT-06 (legacy fallback tagging)
- [ ] `tests/test_inventory_engine.py` — covers INVT-04, INVT-05 (filtering and sorting engine)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| *None* | — | — | All phase behaviors have automated unit verification with synthetic mock fixtures. |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 5s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** verified 2026-08-23
