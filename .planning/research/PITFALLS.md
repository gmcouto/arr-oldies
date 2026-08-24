# Pitfalls Research

**Domain:** Media Server Management & *arr Automation CLI
**Researched:** 2026-08-23
**Confidence:** HIGH

## Critical Pitfalls

### Pitfall 1: Missing or Purged History Records

**What goes wrong:**
Some media files in Radarr/Sonarr may not have a corresponding event in `/api/v3/history` if the user migrated libraries, cleared history logs, or imported files prior to history tracking.
**Why it happens:**
History databases in *arr can be purged, or media may have been imported via manual root folder scan without generating standard `downloadFolderImported` events.
**How to avoid:**
When History API correlation fails to find a matching event for a media file:
1. Clearly report the item as "Unknown / No History Found" rather than failing the scan or guessing.
2. In strict mode, offer options to exclude unindexed items or display them in a dedicated warning section.
**Warning signs:**
Empty history responses or missing `data.fileId` in event logs.
**Phase to address:**
Phase 2 & Phase 3 (History API Correlator & Inventory Engine).

---

### Pitfall 2: Re-Downloading Deleted Files Due to Monitored Status

**What goes wrong:**
A user deletes old movie or episode files to free disk space, but within hours, Radarr/Sonarr automatically re-grabs and downloads them again.
**Why it happens:**
Deleting a file from Radarr/Sonarr without unmonitoring the movie/episode/series leaves it in "Monitored / Missing" status, prompting automated RSS / search sync to snatch another copy.
**How to avoid:**
Provide seamless unmonitoring options (e.g. `--unmonitor` on delete, or unmonitor by default during cleanup actions) via `/api/v3/movie` and `/api/v3/series` endpoints.
**Warning signs:**
Disk space drops again after cleanup.
**Phase to address:**
Phase 4 (Safe Action Engine).

---

### Pitfall 3: Inefficient History Pagination & Excessive API Overhead

**What goes wrong:**
Large libraries with 10,000+ movies or 50,000+ episodes take 10+ minutes to scan if the CLI requests history 10 items per page sequentially.
**Why it happens:**
Default page size in Radarr/Sonarr `/api/v3/history` is small (10–20 records). Fetching thousands of pages sequentially over HTTP saturates the *arr internal SQLite database.
**How to avoid:**
1. Fetch history with optimal `pageSize` (e.g., 500-1000 items per page).
2. Use async pagination with concurrency limits (e.g., max 3-5 concurrent requests per instance) to avoid locking *arr's SQLite DB.
3. Query targeted history endpoints where possible (`/api/v3/history/since` or batch history queries).
**Warning signs:**
HTTP 500 / 503 database lock timeouts from Radarr/Sonarr during scan.
**Phase to address:**
Phase 2 (API Client & History Fetcher).

---

### Pitfall 4: Unsafe Deletion & Confirmation Bypass

**What goes wrong:**
A user runs a cleanup command with unintended filters and accidentally wipes active media without realizing it.
**Why it happens:**
Lack of safe defaults or confusing flag names.
**How to avoid:**
- Enforce strict dry-run as default behavior.
- Only mutate state when `--execute` is explicitly provided.
- Present a clear, high-contrast summary table of items to be deleted before requesting explicit `[y/N]` confirmation in interactive mode.
- Require `--yes` only in non-interactive / headless scripts when `--execute` is present.
**Warning signs:**
Users complaining about accidental data loss.
**Phase to address:**
Phase 4 (Safe Action Engine & CLI Guards).

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Skipping History API and reading file mod-times | Simpler API calls | Inaccurate dates (file touches / migrations reset modtime) | Never (strictly violates user requirement) |
| Hardcoding single instance | Faster initial prototype | Entire architecture needs refactoring for multi-instance | Never |
| Sequential synchronous HTTP | Easier code structure | Painfully slow CLI scans | Never |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Radarr API v3/v4 | Assuming `/api/v3/history` supports server-side `eventType=downloadFolderImported` query filter | Fetch history records and filter `eventType` client-side |
| Sonarr API v3/v4 | Assuming episode files are all returned in `/api/v3/series` | Series endpoint only contains metadata; fetch episode files via `/api/v3/episodefile?seriesId={id}` |
| API Authentication | Passing API key in query params `?apikey=` | Use standard header `X-Api-Key: <key>` |

## "Looks Done But Isn't" Checklist

- [ ] **History Correlation:** Often misses events if download client name differs from imported file name — verify correlation by `fileId` and `movieId`/`seriesId`.
- [ ] **Unmonitoring on Delete:** Often deletes the file but leaves movie monitored — verify movie is set to `monitored: false` when requested.
- [ ] **Sonarr Season / Series Hierarchy:** Often treats episodes independently without series context — verify series title and season info are attached to each episode file.
- [ ] **Instance Timeout Resiliency:** Often crashes if one of 5 instances is offline — verify graceful error reporting per instance.

---
*Pitfalls research for: Media Server Management & *arr Automation CLI*
*Researched: 2026-08-23*
