---
phase: 2
slug: async-arr-api-clients-batch-history-fetcher
status: ready
nyquist_compliant: true
wave_0_complete: false
created: 2026-08-23
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.1.1, pytest-asyncio, respx 0.23.1 |
| **Config file** | pyproject.toml |
| **Quick run command** | `.venv/bin/pytest tests/test_clients.py -x` |
| **Full suite command** | `.venv/bin/pytest` |
| **Estimated runtime** | ~1 second |

---

## Sampling Rate

- **After every task commit:** Run `.venv/bin/pytest tests/test_clients.py -x` (or relevant test module)
- **After every plan wave:** Run `.venv/bin/pytest`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | API-01, API-02 | T-02-01 | Secure API Key handling via X-Api-Key headers | unit | `.venv/bin/pytest tests/test_api_models.py` | ❌ W0 | ⬜ pending |
| 02-01-02 | 01 | 1 | API-03, API-04 | T-02-02 | Safe retry backoff without credential leakage | unit | `.venv/bin/pytest tests/test_base_client.py` | ❌ W0 | ⬜ pending |
| 02-02-01 | 02 | 2 | API-01 | — | N/A | integration | `.venv/bin/pytest tests/test_radarr_client.py` | ❌ W0 | ⬜ pending |
| 02-02-02 | 02 | 2 | API-02 | — | N/A | integration | `.venv/bin/pytest tests/test_sonarr_client.py` | ❌ W0 | ⬜ pending |
| 02-02-03 | 02 | 2 | API-03, API-04 | T-02-03 | Resilient multi-instance batch pagination & error isolation | integration | `.venv/bin/pytest tests/test_history_fetcher.py` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_api_models.py` — Radarr & Sonarr Pydantic v2 data models serialization/deserialization
- [ ] `tests/test_base_client.py` — `BaseArrClient` connection pooling, retry policies, lock detection, and auth headers
- [ ] `tests/test_radarr_client.py` — `RadarrClient` movie, moviefile, and history endpoints
- [ ] `tests/test_sonarr_client.py` — `SonarrClient` series, episodefile, episode, and history endpoints
- [ ] `tests/test_history_fetcher.py` — Batch history paginator, lock mitigation, and multi-instance resilience fetcher

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| *None* | — | — | All phase behaviors have automated verification via respx mocking. |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 5s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** verified 2026-08-23
