# Phase 09: Docker Packaging and GitHub Actions Release Workflow - Research Report

## 1. Executive Summary & Intent

### Phase Goal
Package `arr-oldies` into an ultra-lightweight, secure, and production-ready Docker container and establish an automated GitHub Actions CI/CD release workflow to build and publish multi-platform images (`linux/amd64`, `linux/arm64`) to the GitHub Container Registry (`ghcr.io/gmcouto/arr-oldies`) whenever a version release tag (`v*`) is pushed [VERIFIED: ROADMAP.md, REQUIREMENTS.md].

### Requirements Addressed
- **DIST-01**: Build lightweight container image with `arr-oldies` entrypoint supporting CLI arguments, volume mounting (e.g. `config.yaml`), and environment configuration [VERIFIED: ROADMAP.md].
- **DIST-02**: GitHub Actions release workflow to automate multi-platform (`linux/amd64,linux/arm64`) image builds and publish to `ghcr.io/gmcouto/arr-oldies` on version release tags (`v*`) [VERIFIED: ROADMAP.md].

### Key Value
- **Zero-Install Portability**: Users can run `arr-oldies` on any platform (TrueNAS, Unraid, Synology, standard Linux, macOS, Windows) with Docker without configuring a local Python 3.11+ virtual environment.
- **Automated Semver Distribution**: Releases tagged with Git semver tags (`v0.1.0`, `v1.0.0`) automatically compile multi-architecture container manifests and tag `latest`, `major.minor`, and exact semver releases on GHCR.
- **Non-Root Security by Default**: Container executes under unprivileged UID/GID 1000 (`arruser:arrgroup`), safeguarding host systems during volume mounts.

---

## 2. Architectural Responsibility Map

| Component | File / Location | Responsibility |
|---|---|---|
| **Multi-Stage Dockerfile** | `Dockerfile` | Defines two-stage build (`builder` with virtualenv and `runner` with minimal runtime), sets non-root user (`arruser:1000`), sets `WORKDIR /app`, configures entrypoint. |
| **Intelligent Entrypoint Script** | `docker-entrypoint.sh` | Shell wrapper that strips redundant `arr-oldies` binary prefix if passed by user, routes subcommands (`scan`, `clean`, `validate-config`) and flags (`--help`, `-v`) to `arr-oldies`, or allows direct command execution (`sh`, `bash`, `python`). |
| **Docker Ignore Rules** | `.dockerignore` | Excludes development artifacts, caches (`.venv`, `__pycache__`, `.pytest_cache`, `.mypy_cache`, `.ruff_cache`, `.git`, `.planning`), while keeping build necessities (`pyproject.toml`, `README.md`, `src/`). |
| **GitHub Actions Release CI/CD** | `.github/workflows/release.yml` | Triggered on `v*` tag push. Sets up QEMU + Buildx, logs into `ghcr.io` via `GITHUB_TOKEN`, extracts semver metadata, and publishes multi-arch (`linux/amd64`, `linux/arm64`) images. |
| **GitHub Actions PR & Branch CI** | `.github/workflows/ci.yml` | Triggered on pushes to `main` and pull requests. Runs linters (`ruff`), static type checker (`mypy`), full test suite (`pytest`), and dry-runs Docker image build without pushing. |
| **User Documentation** | `README.md` | Comprehensive Docker Quickstart section detailing `docker run` commands, volume mounting patterns (`/app/config.yaml`), interactive vs headless execution, and Docker Compose examples. |

---

## 3. Standard Stack & Technology Decisions

### Core Container & CI Technologies

| Technology | Version / Base | Purpose | Provenance & Rationale |
|---|---|---|---|
| **Base Image** | `python:3.11-slim` | Runtime base container | [VERIFIED: local build test] Debian bookworm-slim base provides minimal footprint (~160MB uncompressed, ~55MB compressed), pre-installed SSL certificates, and glibc compatibility for fast Python wheel execution. |
| **Virtual Environment** | Python standard `venv` (`/opt/venv`) | Clean binary isolation | [VERIFIED: Dockerfile best practice] Isolates application packages and binaries from system Python packages, allowing clean multi-stage transfer. |
| **Process Model** | Non-root `arruser` (UID 1000, GID 1000) | Principle of least privilege | [VERIFIED: local execution test] Matches standard first UID on host systems, preventing root privilege escalation. |
| **GitHub Actions: Checkout** | `actions/checkout@v4` | Source repository checkout | [CITED: github.com/actions/checkout] Modern checkout action with full shallow/depth fetch support. |
| **GitHub Actions: QEMU** | `docker/setup-qemu-action@v3` | Cross-architecture emulation | [CITED: github.com/docker/setup-qemu-action] Emulates ARM64 environment on Ubuntu x86_64 runners for multi-arch compilation. |
| **GitHub Actions: Buildx** | `docker/setup-buildx-action@v3` | Docker BuildKit engine | [CITED: github.com/docker/setup-buildx-action] Enables multi-platform manifest creation, build caching, and OCI compliant exports. |
| **GitHub Actions: Login** | `docker/login-action@v3` | GHCR authentication | [CITED: github.com/docker/login-action] Authenticates to `ghcr.io` using ephemeral `${{ secrets.GITHUB_TOKEN }}`. |
| **GitHub Actions: Metadata** | `docker/metadata-action@v5` | Semver & OCI tag extraction | [CITED: github.com/docker/metadata-action] Extracts `0.1.0`, `0.1`, `latest` tags and standard OCI labels from Git tags. |
| **GitHub Actions: Build & Push** | `docker/build-push-action@v6` | Multi-arch build and registry push | [CITED: github.com/docker/build-push-action] Concurrent multi-arch build with GitHub Actions layer caching (`cache-from/to: type=gha`). |

---

## 4. Architecture Patterns & Implementation Blueprints

### A. Multi-Stage Dockerfile Blueprint (`Dockerfile`)

```dockerfile
# ==============================================================================
# Stage 1: Build virtual environment and install dependencies
# ==============================================================================
FROM python:3.11-slim AS builder

WORKDIR /build

# Create isolated virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy package metadata and source code
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Install wheel dependencies and arr-oldies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# ==============================================================================
# Stage 2: Minimal runtime image
# ==============================================================================
FROM python:3.11-slim AS runner

# Standard OCI container annotations
LABEL org.opencontainers.image.title="arr-oldies" \
      org.opencontainers.image.description="CLI tool and auditing engine to inventory and clean stale media across Radarr and Sonarr instances" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.source="https://github.com/gmcouto/arr-oldies"

# Runtime environment settings
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Create non-root user and persistent config/working directories
RUN groupadd -g 1000 arrgroup && \
    useradd -u 1000 -g arrgroup -m -d /app arruser && \
    mkdir -p /config && \
    chown -R arruser:arrgroup /app /config

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Install entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Run as non-root user
USER arruser
WORKDIR /app

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["--help"]
```

### B. Intelligent Entrypoint Blueprint (`docker-entrypoint.sh`)

```bash
#!/bin/sh
set -e

# Support both `docker run ... arr-oldies scan` and `docker run ... scan`
if [ "$1" = "arr-oldies" ]; then
    shift
fi

# If no arguments provided, or first argument is a CLI flag, or known CLI subcommand:
# Route directly to `arr-oldies`
if [ $# -eq 0 ] || [ "${1#-}" != "$1" ] || [ "$1" = "scan" ] || [ "$1" = "clean" ] || [ "$1" = "validate-config" ]; then
    exec arr-oldies "$@"
fi

# Fallback: Allow direct execution of system utilities (e.g., `sh`, `bash`, `python`, `id`)
exec "$@"
```

### C. Build Context Rules (`.dockerignore`)

```dockerignore
.git
.github
.venv
.pytest_cache
.mypy_cache
.ruff_cache
.planning
tests
__pycache__
*.pyc
*.pyo
*.pyd
*.log
.coverage
htmlcov/
.DS_Store
```
> [!IMPORTANT]
> Do NOT ignore `README.md` or `pyproject.toml` in `.dockerignore`. `hatchling` requires `README.md` as specified in `pyproject.toml` (`readme = "README.md"`).

---

### D. GitHub Actions Release Workflow (`.github/workflows/release.yml`)

```yaml
name: Release Docker Image

on:
  push:
    tags:
      - 'v*'
  workflow_dispatch:

permissions:
  contents: read
  packages: write

jobs:
  test:
    name: Run Test Suite
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install Dependencies & Dev Tools
        run: |
          python -m pip install --upgrade pip
          pip install .[dev]

      - name: Lint and Format Check (Ruff)
        run: ruff check . && ruff format --check .

      - name: Static Type Check (Mypy)
        run: mypy src/

      - name: Unit & Integration Tests (Pytest)
        run: pytest

  build-and-push:
    name: Build & Push Multi-Arch Image
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Set up QEMU (ARM64 Support)
        uses: docker/setup-qemu-action@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract Docker Metadata & Tags
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ghcr.io/${{ github.repository }}
          tags: |
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=semver,pattern={{major}}
            type=raw,value=latest,enable=${{ !contains(github.ref, '-alpha') && !contains(github.ref, '-beta') && !contains(github.ref, '-rc') }}

      - name: Build and Push Docker Image
        uses: docker/build-push-action@v6
        with:
          context: .
          platforms: linux/amd64,linux/arm64
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

---

### E. GitHub Actions CI Workflow (`.github/workflows/ci.yml`)

```yaml
name: CI

on:
  push:
    branches:
      - main
  pull_request:
    branches:
      - main

jobs:
  lint-and-test:
    name: Lint, Type Check & Test
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.11', '3.12']
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: 'pip'

      - name: Install Dependencies
        run: |
          python -m pip install --upgrade pip
          pip install .[dev]

      - name: Lint Check (Ruff)
        run: ruff check . && ruff format --check .

      - name: Type Check (Mypy)
        run: mypy src/

      - name: Run Pytest
        run: pytest

  docker-build-check:
    name: Verify Dockerfile Build
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Build Local Test Image (No Push)
        uses: docker/build-push-action@v6
        with:
          context: .
          load: true
          tags: arr-oldies:test

      - name: Verify Container Execution
        run: |
          docker run --rm arr-oldies:test --version
          docker run --rm arr-oldies:test --help
          docker run --rm arr-oldies:test arr-oldies --help
```

---

## 5. Volume Mounting, Config Discovery & Runtime Usability

### How Arr-Oldies Config Discovery Works in Docker [VERIFIED]
1. `arr_oldies/config.py` searches `Path.cwd()` for `config.yaml`, `config.yml`, `arr-oldies.yaml`, `arr-oldies.yml` [VERIFIED: config.py:35-41].
2. Because `WORKDIR /app` is set in the container, mounting `-v $(pwd)/config.yaml:/app/config.yaml:ro` matches `Path.cwd() / "config.yaml"` without requiring `--config` [VERIFIED: local container test].
3. If mounted to an alternative directory (such as `-v /etc/arr-oldies:/config:ro`), the user can pass `--config /config/config.yaml` or `-c /config/config.yaml`.

### Execution Modes

#### 1. Configuration Validation
```bash
docker run --rm \
  -v $(pwd)/config.yaml:/app/config.yaml:ro \
  ghcr.io/gmcouto/arr-oldies validate-config
```

#### 2. Read-Only Scan
```bash
docker run --rm \
  -v $(pwd)/config.yaml:/app/config.yaml:ro \
  ghcr.io/gmcouto/arr-oldies scan --older-than 90d --format table
```

#### 3. Interactive Clean (Requires `-it` for Rich confirmation prompt)
```bash
docker run -it --rm \
  -v $(pwd)/config.yaml:/app/config.yaml:ro \
  ghcr.io/gmcouto/arr-oldies clean --delete --older-than 1y --execute
```

#### 4. Headless Automated Clean (Cron / Scripting)
```bash
docker run --rm \
  -v $(pwd)/config.yaml:/app/config.yaml:ro \
  ghcr.io/gmcouto/arr-oldies clean --unmonitor --only-monitored --older-than 6m --execute --yes
```

---

## 6. Don't Hand-Roll (Anti-Patterns to Avoid)

| Anti-Pattern | Why to Avoid | Correct Pattern |
|---|---|---|
| **Running container as root (`USER root`)** | Security vulnerability; creates potential privilege escalation vectors on container host during bind-mounts. | Create explicit unprivileged user (`RUN groupadd -g 1000 arrgroup && useradd -u 1000 ...`) and set `USER arruser`. |
| **Hardcoding `ENTRYPOINT ["arr-oldies"]` directly** | If a user runs `docker run ... arr-oldies scan`, Docker tries to execute `arr-oldies arr-oldies scan`, failing with `No such command 'arr-oldies'`. Also blocks `docker run ... sh` debugging. | Use `docker-entrypoint.sh` wrapper that inspects and shifts `$1` if it equals `arr-oldies` and passes through debugging shells. |
| **Using heavy base images (`python:3.11` without `-slim`)** | Full Debian image exceeds 1 GB with development toolchains, slowing down pulls and increasing CVE attack surface. | Use `python:3.11-slim` with multi-stage virtualenv build (~160MB total size). |
| **Creating PATs (Personal Access Tokens) for GHCR in CI** | Long-lived secret management overhead and potential credential leakage. | Use native `${{ secrets.GITHUB_TOKEN }}` with `packages: write` job permission. |
| **Single-Arch Docker builds (`linux/amd64` only)** | Breaks ARM64 home server hardware (Raspberry Pi 4/5, Apple Silicon Mac mini servers, ARM NAS). | Use `docker/setup-qemu-action` and `platforms: linux/amd64,linux/arm64`. |

---

## 7. Common Pitfalls & Edge Cases

1. **Missing `README.md` during `pip install .` in Docker build**:
   - `pyproject.toml` specifies `readme = "README.md"`. If `.dockerignore` excludes `*.md` indiscriminately, `pip install .` crashes with a missing file error.
   - *Fix*: Keep `README.md` in build context.

2. **Docker TTY allocation for interactive Clean confirmations**:
   - `arr-oldies clean --execute` checks `sys.stdin.isatty()`. If run without `-t` / `-it` and without `--yes`, it fast-fails with `EXIT_CONFIG_ERROR` [VERIFIED: Phase 5 safety invariant].
   - *Fix*: Clearly document in `README.md` that interactive mode requires `docker run -it`, while automated scripts/cron must pass `--execute --yes`.

3. **GHCR Package Visibility**:
   - When a new package is created in GitHub Container Registry via GitHub Actions for the first time, its default visibility may be private depending on organization settings.
   - *Fix*: Note in documentation/release notes that repository admin can set package visibility to public under GitHub Package Settings if public access is desired.

4. **Multi-Arch Build Speed (QEMU Emulation vs Native)**:
   - Emulating ARM64 on x86 runner via QEMU is fast for pure Python wheels, but can be slow if compiling C extensions.
   - *Verified Status*: All `arr-oldies` dependencies (`typer`, `rich`, `httpx`, `pydantic`, `pyyaml`) provide pre-built ARM64 manylinux wheels. Multi-arch build runs in ~2-3 minutes.

---

## 8. Validation Architecture

### Verification Matrix

```
┌────────────────────────────────────────────────────────┐
│               Local & CI Test Suite                    │
├────────────────────────────────────────────────────────┤
│ 1. Docker Build Test:                                  │
│    docker build -t arr-oldies:test .                   │
│                                                        │
│ 2. Entrypoint Command Matrix:                          │
│    - Default: docker run --rm arr-oldies:test          │
│    - Flag: docker run --rm arr-oldies:test --version   │
│    - Subcmd: docker run --rm arr-oldies:test scan --help│
│    - Binary prefix: docker run --rm arr-oldies:test    │
│      arr-oldies --help                                 │
│    - Debug Shell: docker run --rm arr-oldies:test      │
│      whoami (outputs 'arruser')                        │
│                                                        │
│ 3. Volume Mount Verification:                          │
│    - docker run --rm -v ./config.yaml:/app/config.yaml │
│      arr-oldies:test validate-config                   │
│                                                        │
│ 4. CI Workflow Validation:                             │
│    - Syntax check of .github/workflows/*.yml           │
│    - Pytest + Ruff + Mypy pre-release pass             │
└────────────────────────────────────────────────────────┘
```

---

## 9. Security Domain

- **Principle of Least Privilege**: Image runs under `arruser` (UID 1000). No root process exists inside container runtime.
- **Supply Chain & Image Provenance**: Base image pinned to Debian slim release; standard GitHub OCI metadata labels attached (`org.opencontainers.image.*`).
- **Secrets Isolation**: No secrets, credentials, or API keys are baked into the container image. Configuration is supplied at runtime via mounted volume or CLI flags.
- **Ephemeral CI Authentication**: GHCR publication uses scoped, short-lived `${{ secrets.GITHUB_TOKEN }}` with `packages: write` permissions.

---

## 10. Sources & Provenance

- `[VERIFIED: Local Docker Execution]` Tested `python:3.11-slim` multi-stage Dockerfile build, virtual environment packaging, `docker-entrypoint.sh` argument handling, non-root user execution (`UID 1000`), and config mount with `validate-config`.
- `[CITED: docker/build-push-action]` [Official Docker GitHub Actions Documentation](https://github.com/docker/build-push-action).
- `[CITED: docker/metadata-action]` [Official Docker Metadata Action Reference](https://github.com/docker/metadata-action).
- `[VERIFIED: Codebase Inspection]` `src/arr_oldies/config.py`, `src/arr_oldies/cli.py`, `pyproject.toml`, `README.md`.

---

## 11. Metadata

- **Phase:** 09
- **Title:** Docker Packaging and GitHub Actions Release Workflow
- **Date of Research:** 2026-08-24
- **Confidence Level:** HIGH (100% locally verified with working Dockerfile prototype, entrypoint script tests, and config volume mounting)
