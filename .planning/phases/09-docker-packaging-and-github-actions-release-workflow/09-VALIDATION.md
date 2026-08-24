---
phase: 09
slug: docker-packaging-and-github-actions-release-workflow
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-08-24
---

# Phase 09 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x / Docker CLI / GitHub Actions workflow linter |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `pytest tests/ -q` |
| **Full suite command** | `pytest && docker build -t arr-oldies:test . && docker run --rm arr-oldies:test --help` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -q`
- **After every plan wave:** Run `pytest && docker build -t arr-oldies:test . && docker run --rm arr-oldies:test --help`
- **Before `/gsd-verify-work`:** Full suite and docker container tests must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 09-01-01 | 01 | 1 | DIST-01 | T-09-01 | Non-root UID 1000 execution, minimal footprint, proper signal & entrypoint handling | smoke/integration | `docker build -t arr-oldies:test . && docker run --rm arr-oldies:test --help && docker run --rm arr-oldies:test whoami` | ❌ W0 | ⬜ pending |
| 09-01-02 | 01 | 1 | DIST-02 | T-09-02 | Scoped GITHUB_TOKEN permissions, multi-arch QEMU+Buildx GHCR push on tags, PR test pipeline | static/syntax | `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/release.yml')); yaml.safe_load(open('.github/workflows/ci.yml'))"` | ❌ W0 | ⬜ pending |
| 09-01-03 | 01 | 1 | DIST-01 | — | Accurate README instructions for Docker run and volume mounting | doc | `grep -q "docker run" README.md && grep -q "ghcr.io" README.md` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `Dockerfile` — multi-stage container build definition
- [ ] `docker-entrypoint.sh` — container CLI argument wrapper
- [ ] `.dockerignore` — ignore unneeded build context
- [ ] `.github/workflows/release.yml` — release workflow
- [ ] `.github/workflows/ci.yml` — CI workflow

*If none: "Existing infrastructure covers all phase requirements."*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| GHCR Tag Publication | DIST-02 | Requires live GitHub repo tag push with repository permissions | Create git tag `v0.1.0-test` and observe GitHub Actions runner execute buildx push |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
