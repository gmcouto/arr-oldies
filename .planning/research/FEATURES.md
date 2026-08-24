# Feature Research

**Domain:** Media Server Management & *arr Automation CLI
**Researched:** 2026-08-23
**Confidence:** HIGH

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Multi-Instance Configuration | Media hoarders run 2-5+ instances (e.g. Radarr Standard, Radarr 4K, Sonarr TV, Sonarr Anime) | LOW | YAML config supporting instance name, base URL, API key, and service type (`radarr` or `sonarr`) |
| Concurrent API Scanning | Querying multiple remote instances sequentially is too slow | MEDIUM | Concurrent async fetching of movie lists, series lists, and episode files |
| Deep History Event Matching | Determining exact download/import timestamps requires parsing `/api/v3/history` | HIGH | Correlate `downloadFolderImported` / `grabbed` events to active `movieFileId` / `episodeFileId` |
| Oldest-First Sorting & Filtering | The primary goal is finding the oldest media on disk | LOW | Sort by import date or grab date; filter by instance, media type (movie vs episode/series), min size, max age |
| Rich CLI Table Output | High visibility into media title, instance, size, import date, grab date, age | LOW | Clean formatted terminal tables with color coding and human-readable units (GB/TB, days/years) |
| Dry-Run Safety by Default | Accidental deletion in media servers is catastrophic | LOW | Default invocation only audits and prints; zero mutations unless `--execute` is specified |

### Differentiators (Competitive Advantage)

Features that set the product apart. Not required, but valuable.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Safe Execute & Unmonitor Actions | Directly act on stale media without manually clicking 50 items in Web UIs | MEDIUM | Deletes media file via API and optionally sets `monitored: false` to prevent immediate re-download |
| Scriptable JSON / CSV Export | Integration into external backup / alerting scripts | LOW | Structured JSON/CSV output with `--format=json` / `--format=csv` |
| History Gap Detection & Handling | Media imported before history logging or where history was purged | MEDIUM | Flag items with missing history logs gracefully, reporting history status |
| Aggregate Storage Analytics | Summary stats showing total space consumed by age bracket per instance | LOW | Instant breakdown: "Movies older than 2 years: 4.2 TB across 3 instances" |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem good but create problems.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Direct OS File Deletion | Appears faster than API calls | Leaves Radarr/Sonarr databases desynchronized; triggers automatic re-grabs if monitored | Always delete via `/api/v3/moviefile/{id}` and `/api/v3/episodefile/{id}` |
| Unattended Daemon / Automated Cron Delete | Users want automated storage maintenance | Unattended deletion without review can wipe favorite shows if retention rules are misconfigured | Require explicit `--execute --yes` CLI invocation in cron jobs with strict filter flags |
| Web UI / Dashboard | Some users prefer browser GUIs | Adds heavy frontend dependencies, auth layer, maintenance overhead | Keep as a clean, fast, standalone CLI tool |

## Feature Dependencies

```
[Multi-Instance Config]
    └──requires──> [*arr API Client (Radarr & Sonarr)]
                        └──requires──> [History Correlator Engine]
                                           └──requires──> [Catalog & Inventory Index]
                                                               ├──requires──> [CLI Table & Export Output]
                                                               └──requires──> [Safe Action Executor (Delete/Unmonitor)]
```

### Dependency Notes

- **API Client requires Multi-Instance Config:** Needs valid endpoints and API keys.
- **History Correlator Engine requires API Client:** History logs and file records must be retrieved before correlation.
- **Catalog & Inventory Index requires History Correlator Engine:** The unified model brings together file size, instance tag, and historical timestamps.
- **Safe Action Executor requires Catalog Index:** Actions must target verified file IDs and instance endpoints.

## MVP Definition

### Launch With (v1)

Minimum viable product — what's needed to validate the concept.

- [ ] YAML/JSON configuration loading and validation
- [ ] Async client for Radarr (v3/v4) and Sonarr (v3/v4)
- [ ] History API retrieval and correlation to movie/episode files
- [ ] Sorting by oldest import/download date with filters (instance, type, limit, min-age)
- [ ] Rich CLI tabular output with summary statistics
- [ ] Safe execution engine (dry-run by default, `--execute` with interactive confirmation, `--yes` for non-interactive scripts)

### Add After Validation (v1.x)

Features to add once core is working.

- [ ] JSON / CSV export options (`--format=json`, `--format=csv`)
- [ ] Series-level aggregation (e.g. identify entire series where all episodes are older than N months)
- [ ] Unmonitor-only batch action (`--unmonitor-only` without deleting files)

### Future Consideration (v2+)

Features to defer.

- [ ] Interactive TUI with keyboard multi-selection (using Textual)
- [ ] Webhook notifications on execution (Discord / Telegram)

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Multi-Instance Config Parser | HIGH | LOW | P1 |
| Radarr/Sonarr Async API Client | HIGH | MEDIUM | P1 |
| History API Correlator | HIGH | MEDIUM | P1 |
| CLI Table Display & Filters | HIGH | LOW | P1 |
| Safe Action Engine (Dry-run/Execute) | HIGH | MEDIUM | P1 |
| JSON/CSV Export | MEDIUM | LOW | P2 |
| Series Aggregation Mode | MEDIUM | MEDIUM | P2 |

---
*Feature research for: Media Server Management & *arr Automation CLI*
*Researched: 2026-08-23*
