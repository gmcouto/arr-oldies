# Arr-Oldies

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Docker Image](https://img.shields.io/badge/docker-ghcr.io%2Fgmcouto%2Farr--oldies-blue.svg?logo=docker)](https://github.com/gmcouto/arr-oldies/pkgs/container/arr-oldies)
[![Platforms](https://img.shields.io/badge/platforms-linux%2Famd64%20%7C%20linux%2Farm64-lightgrey.svg)](https://github.com/gmcouto/arr-oldies/pkgs/container/arr-oldies)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Type checked: mypy](https://img.shields.io/badge/type_checked-mypy-blue.svg)](https://mypy-lang.org/)

**Arr-Oldies** is a CLI tool and auditing engine that connects across multiple Radarr and Sonarr instances to inventory downloaded media files, correlate them with precise download and import event timestamps from the *arr History API, and list media files sorted by oldest downloads/imports.

It enables self-hosters and media server administrators to inspect media age distribution, filter by audio language and explicit instance types, and safely execute targeted actions (deleting files, unmonitoring shows or individual episodes, or removing full library entries) with robust dry-run defaults.

---

## Features

- **Multi-Instance Support**: Query multiple Radarr and Sonarr instances concurrently with isolated error handling and independent timeouts.
- **History API Correlation**: Correlates media files with exact `downloadFolderImported` / `movieFileImported` and `grabbed` events from the *arr History API, calculating exact age in days.
- **Legacy Fallback**: Gracefully flags and tracks legacy unindexed items added before history retention windows or via manual file imports.
- **Rich Terminal UI**: High-contrast tables and summary cards with color-coded age tiers, instance badges, audio language highlighting, and potential disk space reclamation metrics.
- **Audio Language Filtering & Normalization**: Filter media by audio track language supporting ISO 639-1, ISO 639-2, standard language names, and common aliases (e.g. `-l ja`, `-l japanese`, `-l en`, `-l pt-br`).
- **Flexible Filters & Sorting**:
  - Filter by media type (`movie`, `episode`), monitored status (`--monitored`, `--unmonitored`), size range (`--min-size 2GB`, `--max-size 10GB`), compound age cutoff (`--older-than 1y1m1d`, `--newer-than 90d`, `6m2w`), or calendar dates (`--before 2023-01-01`).
  - Sort by `import_date`, `grab_date`, `size`, `title`, or `age` in ascending or descending order.
- **Safe Action Engine (`clean`)**:
  - **Dry-Run by Default**: Simulates proposed deletions and unmonitoring without mutating any data unless explicit `--execute` is supplied.
  - **Granular Unmonitoring**: Unmonitor specific matched files (individual episodes in Sonarr, movies in Radarr) with `--unmonitor`, unmonitor whole seasons with `--unmonitor-season`, or unmonitor entire parent shows with `--unmonitor-series`.
  - **Safety Ordering**: Automatically unmonitors media in *arr before deleting files to prevent automatic re-download snatch loops.
  - **Interactive Safeguards**: High-contrast warning confirmation prompt (`[y/N]`) before applying mutations.
  - **Automated / Headless Mode**: Fast-fails if `--execute` is run in non-interactive stdin without `-y`/`--yes` to prevent hung cron jobs or subprocess deadlocks.
- **Machine-Readable JSON Output**: Stream pure, unpolluted JSON to stdout with `--format json` while routing progress spinners and warnings to stderr.

---

## Installation

### Docker Quickstart (Recommended)

Arr-Oldies is published as a multi-architecture container image (`linux/amd64`, `linux/arm64`) to GitHub Container Registry (GHCR). You can run it directly without installing a local Python environment.

#### Image Repository
```bash
ghcr.io/gmcouto/arr-oldies:latest
```

#### Volume Mounting & Configuration Discovery
Arr-Oldies automatically searches `/app/config.yaml` inside the container. Mounting your host configuration to `/app/config.yaml:ro` allows zero-flag execution. Passing `-t` allocates a pseudo-TTY so Rich formats tables and summary cards in full ANSI color.

1. **Validate Config**:
   ```bash
   docker run -t --rm \
     -v $(pwd)/config.yaml:/app/config.yaml:ro \
     ghcr.io/gmcouto/arr-oldies validate-config
   ```

2. **Scan Media**:
   ```bash
   docker run -t --rm \
     -v $(pwd)/config.yaml:/app/config.yaml:ro \
     ghcr.io/gmcouto/arr-oldies scan --older-than 90d --format table
   ```

3. **Interactive Clean (Requires `-it`)**:
   When running interactive deletions/unmonitoring with confirmation prompts, pass `-it` to allocate a pseudo-TTY and attach stdin:
   ```bash
   docker run -it --rm \
     -v $(pwd)/config.yaml:/app/config.yaml:ro \
     ghcr.io/gmcouto/arr-oldies clean --delete --older-than 1y --execute
   ```

4. **Automated / Headless Clean (Cron & Scripts)**:
   For automated scripts or cron jobs, supply `-y`/`--yes` alongside `--execute`:
   ```bash
   docker run -t --rm \
     -v $(pwd)/config.yaml:/app/config.yaml:ro \
     ghcr.io/gmcouto/arr-oldies clean --unmonitor --only-monitored --older-than 6m --execute --yes
   ```

5. **Custom Config Path / Volume**:
   ```bash
   docker run -t --rm \
     -v /path/to/custom-config.yaml:/config/config.yaml:ro \
     ghcr.io/gmcouto/arr-oldies --config /config/config.yaml scan
   ```

6. **Docker Compose**:
   ```yaml
   services:
     arr-oldies:
       image: ghcr.io/gmcouto/arr-oldies:latest
       container_name: arr-oldies
       tty: true
       volumes:
         - ./config.yaml:/app/config.yaml:ro
       command: scan --older-than 90d
   ```

#### Interactive CLI Mode & Shell Aliases

If you plan to run multiple `arr-oldies` commands without repeating the `docker run` command prefix:

- **Option A: Drop into an Interactive Container Shell**
  ```bash
  docker run -it --rm \
    -v $(pwd)/config.yaml:/app/config.yaml:ro \
    ghcr.io/gmcouto/arr-oldies sh
  ```
  Once inside the container shell, run subcommands directly:
  ```sh
  /app $ arr-oldies validate-config
  /app $ arr-oldies scan --older-than 90d
  /app $ arr-oldies clean --delete --older-than 1y
  /app $ exit
  ```

- **Option B: Shell Alias (Native CLI Experience)**
  Add an alias to your shell profile (`~/.bashrc` or `~/.zshrc`):
  ```bash
  alias arr-oldies="docker run -it --rm -v \$(pwd)/config.yaml:/app/config.yaml:ro ghcr.io/gmcouto/arr-oldies"
  ```
  Then invoke `arr-oldies` directly from your host terminal:
  ```bash
  arr-oldies validate-config
  arr-oldies scan --older-than 90d
  arr-oldies clean --delete --older-than 2y --execute
  ```

---

### Install from Source

#### Prerequisites
- Python 3.11+
- Access to one or more Radarr (v3/v4) and/or Sonarr (v3/v4) instances with API keys.

```bash
git clone https://github.com/gmcouto/arr-oldies.git
cd arr-oldies

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies and the CLI package
pip install -e .
```

---

## Configuration

Arr-Oldies uses a YAML configuration file to define connection parameters and API credentials for your instances.

### Configuration File Search Precedence
When `--config` is not explicitly passed, Arr-Oldies searches for configuration files in the following order:
1. Current working directory: `./arr-oldies.yaml`, `./arr-oldies.yml`, `./config.yaml`, `./config.yml`
2. User configuration directory: `~/.config/arr-oldies/config.yaml`, `config.yml`, `arr-oldies.yaml`, `arr-oldies.yml`

### Sample Configuration (`config.yaml`)

```yaml
defaults:
  timeout: 45.0       # Global HTTP request timeout (seconds)
  verify_ssl: true    # Verify SSL certificates

instances:
  - name: radarr-main
    type: radarr
    url: http://192.168.1.100:7878
    api_key: your_radarr_api_key_here
    timeout: 60.0

  - name: radarr-4k
    type: radarr
    url: http://192.168.1.100:7879
    api_key: your_radarr_4k_api_key_here

  - name: sonarr-tv
    type: sonarr
    url: https://sonarr.local:8989
    api_key: your_sonarr_api_key_here
    verify_ssl: false  # Optional: disable SSL verification for self-signed certificates
```

---

## CLI Usage & Commands

### 1. `validate-config`
Test configuration file syntax, network connectivity, API authentication, and endpoint health for all or targeted instances.

```bash
# Validate all configured instances
arr-oldies validate-config

# Validate only Radarr instances
arr-oldies validate-config --radarr

# Validate specific instances by name
arr-oldies validate-config -i radarr-main -i sonarr-tv

# Output validation results in pure JSON
arr-oldies validate-config --format json
```

---

### 2. `scan`
Audit media library and list media files sorted by age with filtering and summary metrics.

```bash
# Default audit: lists downloads across all instances sorted by import date (oldest first)
arr-oldies scan

# Scan only Radarr instances with movies older than 1 year, 1 month, and 1 day
arr-oldies scan --radarr --older-than 1y1m1d

# Filter only monitored items with Portuguese/Brazilian audio larger than 1GB
arr-oldies scan --only-monitored -l pt-br --min-size 1GB -s size --order desc

# Target top 20 oldest TV episodes imported before 2023
arr-oldies scan --sonarr --type episode --before 2023-01-01 --limit 20

# Export scan results to JSON for piping into jq or custom scripts
arr-oldies scan --format json > audit.json
```

#### Scan Options:
- `--radarr` / `--sonarr`: Filter targets by instance type.
- `-i, --instance <name>`: Target specific instance name(s) (repeatable).
- `-t, --type <movie|episode>`: Filter by media type.
- `-l, --audio-lang <lang>`: Filter by audio language (repeatable, e.g. `-l ja -l en -l pt-br`).
- `--monitored` / `--only-monitored`: Filter only monitored media items.
- `--unmonitored` / `--only-unmonitored`: Filter only unmonitored media items.
- `--min-size <size>` / `--max-size <size>`: File size bounds (e.g. `500MB`, `2GiB`, `1.5TB`).
- `--older-than <cutoff>` / `--newer-than <cutoff>`: Relative age cutoff supporting compound formats (e.g. `30d`, `6m2w`, `1y1m1d`).
- `--before <date>` / `--after <date>`: Absolute ISO date filter (e.g. `2023-01-01`).
- `--legacy` / `--history`: Filter exclusively for legacy unindexed items or items with verified history events.
- `-s, --sort <field>`: Sort by `import_date`, `grab_date`, `size`, `title`, `age` (default: `import_date`).
- `--sort-dir <asc|desc>`: Sort direction (default: `asc`).
- `-n, --limit <int>`: Limit output to top N items.
- `-f, --format <table|json>`: Output format (default: `table`).
- `--summary / --no-summary`: Toggle summary metrics panel display.

---

### 3. `clean`
Safely execute targeted write actions (`--delete`, `--unmonitor`, `--unmonitor-season`, `--unmonitor-series`, `--remove`) on media matching filter criteria.

> [!IMPORTANT]
> **Safety Guard**: `arr-oldies clean` runs in **dry-run simulation mode by default**. No files are deleted and no *arr settings are modified unless you explicitly pass the `--execute` flag.

```bash
# 1. DRY-RUN SIMULATION (Default)
# Simulates deletion of all movies older than 2 years with Japanese audio
arr-oldies clean --delete --radarr --older-than 2y -l ja

# 2. UNMONITOR ONLY ACTIVE / MONITORED EPISODES
# Identifies and unmonitors only monitored episodes older than 180 days (skipping already unmonitored)
arr-oldies clean --unmonitor --only-monitored --sonarr --older-than 180d --execute

# 3. UNMONITOR WHOLE SEASON IN SONARR
# Unmonitors the entire season for matched old episode items
arr-oldies clean --unmonitor-season --sonarr --older-than 1y --execute

# 4. UNMONITOR ENTIRE SERIES IN SONARR
# Unmonitors full parent series for matched old episode items
arr-oldies clean --unmonitor-series --sonarr --older-than 2y --execute

# 5. INTERACTIVE DELETION
# Prompts with a confirmation warning modal [y/N] before making changes
arr-oldies clean --delete --unmonitor --older-than 3y --execute

# 6. HEADLESS AUTOMATION / CRON EXECUTION
# Bypasses interactive confirmation with --yes
arr-oldies clean --delete --unmonitor --older-than 2y --limit 50 --execute --yes
```

#### Action Flags (at least one required):
- `--delete`: Delete the media file(s) via the *arr REST API.
- `--unmonitor`: Unmonitor matched media items (movies in Radarr, specific episodes in Sonarr).
- `--unmonitor-season`: Unmonitor entire season in Sonarr for matched episode items.
- `--unmonitor-series`: Unmonitor entire parent TV series in Sonarr for matched episode items.
- `--remove`: Remove complete movie or series library entry from the *arr database.

#### Target & Filter Flags:
- `--monitored` / `--only-monitored`: Target only monitored media items.
- `--unmonitored` / `--only-unmonitored`: Target only unmonitored media items.
- `--older-than` / `--newer-than`: Relative age cutoffs (e.g. `30d`, `6m`, `1y1m1d`).
- Other filters (`--radarr`, `--sonarr`, `-i`, `-t`, `-l`, `--min-size`, `--max-size`, `--before`, `--after`, `-s`, `-n`, `-f`) identical to `scan`.

#### Safety Flags:
- `--execute`: Execute the mutations on the *arr instance (defaults to dry-run simulation).
- `-y, --yes`: Bypass interactive confirmation prompt (required for headless / cron scripts).

---

## Development & Testing

### Running Tests
The project comes with a comprehensive suite of unit and integration tests using `pytest` and `respx` for mock *arr API responses.

```bash
# Run full test suite
pytest -v

# Run with coverage report
pytest --cov=src/arr_oldies -v
```

### Code Formatting & Type Checking

```bash
# Check code style and formatting with Ruff
ruff check .
ruff format --check .

# Run static type checking with Mypy
mypy src/
```

---

## License

This project is licensed under the MIT License.
