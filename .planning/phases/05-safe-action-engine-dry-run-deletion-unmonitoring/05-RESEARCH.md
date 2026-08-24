# Phase 05: Safe Action Engine (Dry-Run, Deletion & Unmonitoring) — Research

**Phase:** 05 - Safe Action Engine (Dry-Run, Deletion & Unmonitoring)  
**Status:** Ready to Plan  
**Confidence:** HIGH  
**Domain:** Safe *arr mutation pipeline, dry-run simulation, media file deletion, series/movie unmonitoring, episode unmonitoring, library entry removal, and confirmation guards  

---

<user_constraints>
## User Constraints & Decisions

### Project Constraints & Directives
- **C-01:** Tech stack: Python 3.11+ using `httpx>=0.27.0`, `pydantic>=2.7.0`, `rich>=13.7.0`, `typer>=0.12.0`, `pyyaml>=6.0.1`. [CITED: AGENTS.md §Core Technologies]
- **C-02:** Strict API compliance: Rely exclusively on standard Radarr v3/v4 and Sonarr v3/v4 REST APIs (`/api/v3/moviefile`, `/api/v3/episodefile`, `/api/v3/movie/editor`, `/api/v3/series/editor`, `/api/v3/episode/monitor`, `/api/v3/movie`, `/api/v3/series`). Never execute direct filesystem deletions or direct SQLite mutations to avoid desynchronizing *arr state or triggering automatic re-downloads. [CITED: AGENTS.md §Constraints, .planning/REQUIREMENTS.md §Out of Scope]
- **C-03:** Dry-run default (ACT-01): Default to dry-run mode for all mutation commands. The CLI must clearly display simulated actions, affected items, and reclaimable space without modifying *arr databases or deleting files. [CITED: .planning/REQUIREMENTS.md §ACT-01]
- **C-04:** Granular action controls (ACT-02 .. ACT-05): Support independent and composable execution flags:
  - `--delete`: Remove target media file(s) via Radarr/Sonarr file endpoints.
  - `--unmonitor`: Unmonitor target movie or entire TV series without deleting files.
  - `--unmonitor-episode`: Unmonitor specific individual episode(s) in Sonarr without unmonitoring the entire series.
  - `--remove`: Completely remove the movie or series entry from the *arr library database. [CITED: .planning/REQUIREMENTS.md §ACT-02..ACT-05]
- **C-05:** Interactive execution guard (ACT-06): Require explicit `--execute` flag to perform write operations. When `--execute` is specified interactively without `--yes`, present a high-contrast Rich confirmation modal listing target files, action types, and storage space to be freed before requesting user confirmation. [CITED: .planning/REQUIREMENTS.md §ACT-06]
- **C-06:** Headless automation bypass (ACT-07): Support `--yes` / `-y` flag (when combined with `--execute`) to bypass interactive prompts for automated cron jobs and headless scripts. Supplying `--yes` without `--execute` must remain safe in dry-run mode. [CITED: .planning/REQUIREMENTS.md §ACT-07]
- **C-07:** Stderr vs Stdout separation: When `--format json` is active, emit pure parseable JSON to stdout, keeping all status indicators, confirmation prompts, and warning banners on stderr. [VERIFIED: `src/arr_oldies/console.py:12-14`]

### Key Decisions Inherited from Phases 1, 2, 3, & 4
- **D-01:** Unified inventory models: `MediaInventoryItem` in `arr_oldies.inventory.models` contains `movie_id`, `movie_file_id`, `series_id`, `episode_file_id`, and `episode_ids: list[int]`, providing exact target IDs for all *arr mutation endpoints. [VERIFIED: `src/arr_oldies/inventory/models.py:44-89`]
- **D-02:** Multi-instance targeting: `resolve_target_instances` in `arr_oldies.targeting` enables targeting specific apps (`--radarr`, `--sonarr`) or named instances (`-i / --instance`). [VERIFIED: `src/arr_oldies/targeting.py:16-56`]
- **D-03:** Composable filtering & limiting: `InventoryEngine` in `arr_oldies.inventory.engine` provides unified filtering by media type, audio language, size, age, and date cutoffs, plus oldest-first sorting and limit truncation. [VERIFIED: `src/arr_oldies/inventory/engine.py:17-146`]
- **D-04:** Instance resiliency: API clients implement exponential backoff with jitter and isolate per-instance network failures so one failing instance does not crash operations on healthy instances. [VERIFIED: `src/arr_oldies/api/base.py:144-213`]

### Agent's Discretion
- Organization of actions subsystem into `src/arr_oldies/actions/` (`models.py`, `executor.py`, `confirmation.py`, `__init__.py`).
- Exact execution ordering (e.g. unmonitoring before deleting file to prevent *arr re-download race conditions).
- Formatting of the Rich confirmation modal and execution summary report table.
- Structure of the dry-run and execution JSON export payloads.
- Integration of the `clean` CLI command in `src/arr_oldies/cli.py`.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Source | Research Support |
|---|---|---|---|
| **ACT-01** | Default to dry-run mode for all commands, printing exact simulated actions without mutating *arr databases or deleting files | `.planning/REQUIREMENTS.md` §ACT-01 | §1 Deep-Dive: `ActionPlan` simulation generator and dry-run reporting pipeline in `arr_oldies.actions.executor`. |
| **ACT-02** | Implement `--delete` action to remove target media file(s) via Radarr/Sonarr API | `.planning/REQUIREMENTS.md` §ACT-02 | §2 Deep-Dive: `delete_movie_file` (`DELETE /api/v3/moviefile/{id}`) and `delete_episode_file` (`DELETE /api/v3/episodefile/{id}`). |
| **ACT-03** | Implement `--unmonitor` action to unmonitor target movie or entire TV show in *arr without deleting files | `.planning/REQUIREMENTS.md` §ACT-03 | §3 Deep-Dive: `unmonitor_movie` (`PUT /api/v3/movie/editor`) and `unmonitor_series` (`PUT /api/v3/series/editor`). |
| **ACT-04** | Implement `--unmonitor-episode` action to unmonitor specific individual episode(s) in Sonarr without unmonitoring the entire series | `.planning/REQUIREMENTS.md` §ACT-04 | §4 Deep-Dive: `unmonitor_episodes` (`PUT /api/v3/episode/monitor` with `episodeIds`). |
| **ACT-05** | Implement `--remove` action to completely remove the movie or show entry from the *arr library | `.planning/REQUIREMENTS.md` §ACT-05 | §5 Deep-Dive: `delete_movie` (`DELETE /api/v3/movie/{id}`) and `delete_series` (`DELETE /api/v3/series/{id}`). |
| **ACT-06** | Require explicit `--execute` flag to perform write operations, prompting with an interactive Rich confirmation modal listing target files and space to be freed | `.planning/REQUIREMENTS.md` §ACT-06 | §6 Deep-Dive: Rich confirmation panel and interactive `typer.confirm` / prompt guard in `arr_oldies.actions.confirmation`. |
| **ACT-07** | Support `--yes` flag (when combined with `--execute`) to bypass interactive confirmation for automated scripts and headless cron execution | `.planning/REQUIREMENTS.md` §ACT-07 | §7 Deep-Dive: Non-interactive confirmation bypass logic with headless execution reporting in `arr_oldies.cli`. |
</phase_requirements>

---

## Summary

Phase 5 implements the **Safe Action Engine**, completing the core value proposition of Arr-Oldies: moving from auditing and visualization to safe, guarded, granular cleanup of stale media files across multiple Radarr and Sonarr instances.

The primary architectural mandate is **Safety First**:
1. **Dry-Run by Default (ACT-01):** Invoking `arr-oldies clean` without `--execute` generates a complete simulation plan (`ActionPlan`) itemizing every file, movie, series, and episode that would be affected, along with total reclaimable space, without performing any API mutations.
2. **Explicit Mutation Gate (ACT-06):** No write operations are ever sent to Radarr or Sonarr unless `--execute` is explicitly passed on the command line.
3. **Interactive Confirmation Modal (ACT-06):** When running with `--execute`, the CLI presents a high-contrast Rich warning panel summarizing the destructive actions and prompts for explicit confirmation (`[y/N]`).
4. **Headless Automation Support (ACT-07):** For scheduled cron maintenance and script pipelines, `--execute --yes` bypasses the interactive prompt while maintaining full audit logging and machine-readable JSON reporting.
5. **Granular Operations (ACT-02..ACT-05):** Users can independently target file deletion (`--delete`), full show/movie unmonitoring (`--unmonitor`), individual episode unmonitoring (`--unmonitor-episode`), or complete library entry removal (`--remove`).
6. **Race-Condition Prevention:** When deleting media files, unmonitoring is scheduled *before* file deletion so Radarr/Sonarr does not immediately detect missing media and snatch replacement torrents/NZBs.

---

## Architectural Responsibility Map

| Capability | Primary Module | Secondary Tier | Rationale |
|---|---|---|---|
| **Radarr Mutation API** | `arr_oldies.api.radarr.RadarrClient` | `BaseArrClient` | Implements `delete_movie_file`, `unmonitor_movie`, and `delete_movie` via REST endpoints. |
| **Sonarr Mutation API** | `arr_oldies.api.sonarr.SonarrClient` | `BaseArrClient` | Implements `delete_episode_file`, `unmonitor_series`, `unmonitor_episodes`, and `delete_series`. |
| **Action Models & Schemas** | `arr_oldies.actions.models` | `pydantic.BaseModel` | Defines `ActionType`, `ActionItem`, `ActionPlan`, `ActionResult`, and `ExecutionReport`. |
| **Action Planning & Executor** | `arr_oldies.actions.executor` | `MultiInstanceFetcher` | Builds dry-run simulation plans and executes mutation batches in safe dependency order. |
| **Confirmation Modal & Prompts** | `arr_oldies.actions.confirmation` | `rich.panel.Panel` | Formats the pre-execution confirmation modal and manages interactive confirmation prompts. |
| **CLI Clean Command** | `arr_oldies.cli` | Typer CLI Application | Exposes `arr-oldies clean` with targeting, filters, action flags, safety guards, and formatters. |

---

## Standard Stack & Package Legitimacy Audit

### Core Technologies
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `python` | >=3.11 (`3.12.3` in `.venv`) | Core language runtime | Native `StrEnum`, pattern matching, type hints (`X \| None`), and standard `datetime.UTC`. |
| `httpx` | >=0.27.0 (`0.28.1` in `.venv`) | Async HTTP client | Fully async/await native client handling DELETE/PUT requests with connection pooling and retry logic. |
| `rich` | >=13.7.0 (`15.0.0` in `.venv`) | Terminal modals, panels, tables | High-contrast confirmation panels, progress bars, and execution summary reports. |
| `typer` | >=0.12.0 (`0.15.1` in `.venv`) | CLI argument parsing | Clean command routing with type annotations, boolean flags (`--execute`, `--yes`), and confirmation helpers. |
| `pydantic` | >=2.7.0 (`2.13.4` in `.venv`) | Data modeling & validation | Strict validation of action plans, mutation results, and JSON export serialization. |
| `respx` | >=0.21.0 (`0.23.1` in `.venv`) | Mocking HTTPX requests in tests | Deterministic mock testing of Radarr/Sonarr DELETE and PUT endpoints. |

### Package Legitimacy Audit
| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---|---|---|---|---|---|---|
| `httpx` | PyPI | 6 yrs | ~150M/mo | `github.com/encode/httpx` | `[OK]` | Approved (Already in `.venv`) |
| `rich` | PyPI | 5 yrs | ~180M/mo | `github.com/Textualize/rich` | `[OK]` | Approved (Already in `.venv`) |
| `typer` | PyPI | 5 yrs | ~80M/mo | `github.com/fastapi/typer` | `[OK]` | Approved (Already in `.venv`) |
| `pydantic` | PyPI | 8 yrs | ~150M/mo | `github.com/pydantic/pydantic` | `[OK]` | Approved (Already in `.venv`) |
| `respx` | PyPI | 5 yrs | ~20M/mo | `github.com/lundberg/respx` | `[OK]` | Approved (Already in `.venv`) |

**Packages removed due to [SLOP] verdict:** None  
**Packages flagged as suspicious [SUS]:** None  

---

## Architecture Patterns

### System Architecture Diagram: Safe Action Engine Pipeline

```mermaid
graph TD
    subgraph CLI["1. CLI Invocation (arr_oldies.cli)"]
        User["User Invocation<br/>arr-oldies clean --delete --unmonitor ..."]
        FlagCheck{"Validate Flags<br/>At least 1 action flag?"}
        FilterTarget["Target Instances & Filter Inventory<br/>(reusing Phase 3 InventoryEngine)"]
    end

    subgraph ActionEngine["2. Action Engine (arr_oldies.actions)"]
        BuildPlan["ActionExecutor.build_plan<br/>Construct ActionPlan with ActionItems"]
        ExecuteFlag{"Is --execute<br/>specified?"}
        
        subgraph DryRunPath["Dry-Run Mode (ACT-01)"]
            DryRunTable["Render Dry-Run Simulation Table"]
            DryRunJSON["Export ActionPlan JSON"]
            DryRunNotice["Print [bold yellow]DRY-RUN[/] Notice<br/>Zero mutations applied"]
        end
        
        subgraph ExecutionGuard["Execution Guard (ACT-06, ACT-07)"]
            YesFlag{"Is --yes<br/>specified?"}
            ShowModal["Render High-Contrast Rich Confirmation Modal"]
            UserPrompt{"Interactive Prompt<br/>typer.confirm [y/N]"}
            Abort["Abort: No changes made<br/>Exit Code 0"]
        end
        
        subgraph MutationPipeline["3. Mutation Pipeline (executor.py)"]
            OrderSafe["Order Operations:<br/>1. Unmonitor (Movie/Series/Episode)<br/>2. Delete Media Files<br/>3. Remove Library Entries"]
            APIExec["Execute API Calls via RadarrClient / SonarrClient<br/>• DELETE /api/v3/moviefile/{id}<br/>• DELETE /api/v3/episodefile/{id}<br/>• PUT /api/v3/movie/editor<br/>• PUT /api/v3/series/editor<br/>• PUT /api/v3/episode/monitor<br/>• DELETE /api/v3/movie/{id}<br/>• DELETE /api/v3/series/{id}"]
            CollectReport["Collect ActionResult list & build ExecutionReport"]
        end
    end

    subgraph Reporting["4. Output Presentation (arr_oldies.reporting & console)"]
        ExecReportTable["Render Execution Summary Table<br/>(Successes, Failures, Space Freed)"]
        ExecReportJSON["Emit ExecutionReport JSON to stdout"]
    end

    User --> FlagCheck
    FlagCheck -->|Yes| FilterTarget
    FlagCheck -->|No| User
    FilterTarget --> BuildPlan
    BuildPlan --> ExecuteFlag
    
    ExecuteFlag -->|No (Default)| DryRunPath
    ExecuteFlag -->|Yes| YesFlag
    
    YesFlag -->|No| ShowModal
    ShowModal --> UserPrompt
    UserPrompt -->|n / Abort| Abort
    UserPrompt -->|y / Confirm| OrderSafe
    YesFlag -->|Yes| OrderSafe
    
    OrderSafe --> APIExec
    APIExec --> CollectReport
    CollectReport --> ExecReportTable
    CollectReport --> ExecReportJSON
```

---

### Recommended Project Structure
```
src/arr_oldies/
├── actions/                     # NEW subpackage for Phase 5
│   ├── __init__.py              # Package exports
│   ├── confirmation.py          # Rich confirmation modal & prompt logic (ACT-06)
│   ├── executor.py              # ActionExecutor core engine & simulation (ACT-01..05)
│   └── models.py                # ActionType, ActionPlan, ActionItem, ActionResult, ExecutionReport
├── api/
│   ├── base.py                  # Base async HTTPX client
│   ├── factory.py               # Client factory
│   ├── fetcher.py               # MultiInstanceFetcher
│   ├── models.py                # API response models
│   ├── radarr.py                # Extended with delete_movie_file, unmonitor_movie, delete_movie
│   └── sonarr.py                # Extended with delete_episode_file, unmonitor_series/episodes, delete_series
├── inventory/
│   ├── correlator.py            # History correlation
│   ├── engine.py                # Filter & sort engine
│   ├── languages.py             # Language normalization
│   ├── models.py                # MediaInventoryItem, InventoryFilter, InventorySummary
│   └── parser.py                # Size and age parsers
├── reporting/
│   ├── formatters.py            # Units and styling
│   ├── json_export.py           # JSON serialization
│   ├── models.py                # OutputFormat enum
│   ├── summary.py               # Summary panels
│   └── table.py                 # Rich tables
├── cli.py                       # Extended with 'clean' command and action flags
├── config.py                    # YAML configuration loader
├── console.py                   # Rich console instances (stdout/stderr)
├── constants.py                 # API endpoints and defaults
├── exceptions.py                # Domain exceptions
├── models.py                    # InstanceConfig & AppConfig
├── prober.py                    # Health checker
└── targeting.py                 # Instance targeting
tests/
├── test_action_executor.py       # Unit tests for ActionExecutor simulation & mutations
├── test_action_models.py         # Unit tests for action domain schemas
├── test_cli_clean.py             # CLI end-to-end tests (dry-run, --execute, --yes, flags)
├── test_confirmation.py          # Tests for confirmation panel rendering and prompt bypass
├── test_radarr_client_actions.py # Tests for Radarr delete/unmonitor endpoints
└── test_sonarr_client_actions.py # Tests for Sonarr delete/unmonitor endpoints
```

---

### Pattern 1: Action Planning & Dry-Run Simulation Pipeline (ACT-01)

**What:** Before executing any mutation, the system compiles target `MediaInventoryItem` records and selected `ActionType` flags into an immutable `ActionPlan`. In dry-run mode, this plan is displayed as a preview table or exported as JSON without making any write requests.

**When to use:** In `arr_oldies.actions.executor.ActionExecutor.build_plan` and `arr_oldies.cli.clean_command`.

```python
# [VERIFIED: Pattern designed using Pydantic v2 and Rich]
from enum import StrEnum
from pydantic import BaseModel, Field
from arr_oldies.inventory.models import MediaInventoryItem

class ActionType(StrEnum):
    """Supported mutation actions."""
    DELETE = "delete"
    UNMONITOR = "unmonitor"
    UNMONITOR_EPISODE = "unmonitor_episode"
    REMOVE = "remove"

class ActionItem(BaseModel):
    """An individual media item paired with requested action types."""
    item: MediaInventoryItem
    action_types: list[ActionType]

class ActionPlan(BaseModel):
    """Aggregated execution plan detailing all proposed actions."""
    target_actions: list[ActionType]
    items: list[ActionItem] = Field(default_factory=list)
    total_items: int = 0
    total_size_bytes: int = 0
    instances_breakdown: dict[str, int] = Field(default_factory=dict)
    dry_run: bool = True
```

---

### Pattern 2: Atomic Execution & Ordering Safety Guard (ACT-02, ACT-03, ACT-04, ACT-05)

**What:** When executing mutations on an item that has both unmonitoring and file deletion requested, unmonitor operations are executed **before** deleting files. This prevents *arr background sync tasks from detecting a missing file and automatically downloading a replacement.

**Execution Order per Item:**
1. **Unmonitor Show / Movie (`ActionType.UNMONITOR`)**: Set `monitored: false` on the movie or entire series via `/api/v3/movie/editor` or `/api/v3/series/editor`.
2. **Unmonitor Episode (`ActionType.UNMONITOR_EPISODE`)**: Set `monitored: false` on the specific episode(s) via `/api/v3/episode/monitor`.
3. **Delete Media File (`ActionType.DELETE`)**: Call `DELETE /api/v3/moviefile/{id}` or `DELETE /api/v3/episodefile/{id}`.
4. **Remove Library Entry (`ActionType.REMOVE`)**: If full removal is requested, call `DELETE /api/v3/movie/{id}` or `DELETE /api/v3/series/{id}`. (Note: if `--delete` was also specified, `deleteFiles=true` is passed to clean up files simultaneously).

```python
# [VERIFIED: Error resilience and execution ordering]
async def execute_item_actions(
    client: RadarrClient | SonarrClient,
    action_item: ActionItem,
) -> list[ActionResult]:
    """Execute requested actions in strict safe order with per-step error resilience."""
    results: list[ActionResult] = []
    item = action_item.item
    actions = action_item.action_types

    # Step 1: Unmonitor Movie or Series
    if ActionType.UNMONITOR in actions:
        try:
            if isinstance(client, RadarrClient) and item.movie_id:
                await client.unmonitor_movie(item.movie_id)
            elif isinstance(client, SonarrClient) and item.series_id:
                await client.unmonitor_series(item.series_id)
            results.append(ActionResult(item_id=item.id, action_type=ActionType.UNMONITOR, success=True))
        except Exception as exc:
            results.append(ActionResult(item_id=item.id, action_type=ActionType.UNMONITOR, success=False, error_message=str(exc)))

    # Step 2: Unmonitor Episode(s)
    if ActionType.UNMONITOR_EPISODE in actions:
        try:
            if isinstance(client, SonarrClient) and item.episode_ids:
                await client.unmonitor_episodes(item.episode_ids)
                results.append(ActionResult(item_id=item.id, action_type=ActionType.UNMONITOR_EPISODE, success=True))
        except Exception as exc:
            results.append(ActionResult(item_id=item.id, action_type=ActionType.UNMONITOR_EPISODE, success=False, error_message=str(exc)))

    # Step 3: Delete Media File
    if ActionType.DELETE in actions and ActionType.REMOVE not in actions:
        try:
            if isinstance(client, RadarrClient) and item.movie_file_id:
                await client.delete_movie_file(item.movie_file_id)
            elif isinstance(client, SonarrClient) and item.episode_file_id:
                await client.delete_episode_file(item.episode_file_id)
            results.append(ActionResult(item_id=item.id, action_type=ActionType.DELETE, success=True, freed_bytes=item.size_bytes))
        except Exception as exc:
            results.append(ActionResult(item_id=item.id, action_type=ActionType.DELETE, success=False, error_message=str(exc)))

    # Step 4: Remove Library Entry
    if ActionType.REMOVE in actions:
        try:
            delete_files = ActionType.DELETE in actions
            if isinstance(client, RadarrClient) and item.movie_id:
                await client.delete_movie(item.movie_id, delete_files=delete_files)
            elif isinstance(client, SonarrClient) and item.series_id:
                await client.delete_series(item.series_id, delete_files=delete_files)
            results.append(ActionResult(item_id=item.id, action_type=ActionType.REMOVE, success=True, freed_bytes=item.size_bytes if delete_files else 0))
        except Exception as exc:
            results.append(ActionResult(item_id=item.id, action_type=ActionType.REMOVE, success=False, error_message=str(exc)))

    return results
```

---

### Pattern 3: Rich Confirmation Modal & Automated Bypass (ACT-06, ACT-07)

**What:** In interactive mode with `--execute`, render a prominent confirmation modal and require user confirmation (`[y/N]`). When `--yes` is combined with `--execute`, bypass the prompt automatically.

```python
# [VERIFIED: Rich confirmation modal pattern]
from rich import box
from rich.panel import Panel
from rich.table import Table
import typer
from arr_oldies.actions.models import ActionPlan
from arr_oldies.reporting.formatters import format_size

def render_confirmation_panel(plan: ActionPlan) -> Panel:
    """Construct a high-contrast confirmation warning panel."""
    grid = Table.grid(expand=True, padding=(0, 2))
    grid.add_column(style="bold yellow", justify="left")
    grid.add_column(style="bold white", justify="right")

    actions_str = ", ".join(a.value.upper() for a in plan.target_actions)
    grid.add_row("Actions to Perform:", f"[bold red]{actions_str}[/bold red]")
    grid.add_row("Total Items Affected:", f"{plan.total_items:,} items")
    grid.add_row("Potential Space to be Freed:", f"[bold green]{format_size(plan.total_size_bytes)}[/bold green]")
    
    inst_str = ", ".join(f"{k}: {v:,}" for k, v in plan.instances_breakdown.items())
    grid.add_row("Instances Breakdown:", inst_str or "None")

    return Panel(
        grid,
        title="[bold bright_white on red] WARNING: DESTRUCTIVE MUTATION REQUESTED [/bold bright_white on red]",
        border_style="red",
        box=box.ROUNDED,
    )

def prompt_confirmation(plan: ActionPlan, console) -> bool:
    """Display confirmation panel and prompt for user verification."""
    console.print(render_confirmation_panel(plan))
    confirmed = typer.confirm(
        f"Are you sure you want to proceed with executing mutations on {plan.total_items} items?",
        default=False,
    )
    return confirmed
```

---

### Anti-Patterns to Avoid

- **Direct OS Filesystem Deletion:** Using Python's `os.remove()` or `shutil.rmtree()`. This bypasses Radarr/Sonarr internal databases, leaving orphan records and causing *arr to snatch replacement media on its next RSS/search sync. Always delete via official REST API endpoints.
- **Deleting Before Unmonitoring:** If file deletion is executed before unmonitoring, *arr's background file watcher or database refresh could trigger an automated re-download before the unmonitor request completes. Always unmonitor first.
- **Silent Dry-Run Execution:** Executing without `--execute` but failing to clearly state that no changes were made. Always print a prominent dry-run notice in table mode and include `"mode": "dry-run"` in JSON mode.
- **Bypassing Safety on `--yes` Alone:** If a user accidentally specifies `--yes` without `--execute`, the tool MUST NOT execute mutations. `--execute` is the mandatory write gate; `--yes` only controls interactive prompting.
- **Crashing on Single-Item Failure:** If 1 of 50 items fails to delete (e.g. 404 already deleted by external process), failing the entire batch. Collect per-item `ActionResult` errors and proceed with remaining items.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| **Interactive CLI Prompts** | Raw `input("y/n")` loops | `typer.confirm()` | Handles stdin EOF, keyboard interrupts, default answers, and whitespace normalization. |
| **Confirmation Modals** | Custom ASCII box strings | `rich.panel.Panel` + `rich.table.Table.grid` | Automatically handles ANSI coloring, terminal margins, and column alignment. |
| **HTTP Deletion & Modification** | Low-level socket / raw urllib | `httpx.AsyncClient` + `BaseArrClient` | Built-in authentication headers, connection pooling, timeout management, and retry backoff. |
| **Action Plan Serialization** | Ad-hoc dictionary builders | `pydantic.BaseModel.model_dump()` | Type-safe JSON serialization with ISO-8601 datetimes and enum conversion. |

---

## Runtime State Inventory

> Refactor / Rename Check: Phase 5 extends existing API clients and adds the `clean` CLI command. No existing database tables, API schemas, or configuration files are being renamed or deleted.

---

## Common Pitfalls

### Pitfall 1: Re-Downloading Deleted Files Due to Monitored Status
**What goes wrong:** A user runs `arr-oldies clean --delete --execute`, files are removed from disk, but within hours Radarr/Sonarr automatically re-downloads them.  
**Why it happens:** The movie or episode remained monitored in *arr. When the file was deleted, *arr saw it as missing and snatched a new copy from indexers.  
**How to avoid:** Recommend combining `--delete` with `--unmonitor` or `--unmonitor-episode`, and ensure the executor updates monitoring status *before* issuing the file deletion API request.  
**Warning signs:** *arr activity queue suddenly populates with grabs for recently deleted titles.

### Pitfall 2: Accidental Mutation from Misunderstood Flags
**What goes wrong:** A user runs `arr-oldies clean --delete --yes` intending to test, and files are deleted without confirmation.  
**Why it happens:** In poorly designed CLIs, `--yes` implies `--execute`.  
**How to avoid:** Strictly require `--execute` for any write operations. If `--yes` is passed without `--execute`, the command remains in dry-run mode and prints a note explaining that `--execute` is required to perform mutations.  
**Warning signs:** CLI modifying state without explicit `--execute`.

### Pitfall 3: Subprocess Deadlock / Input Blocking in Automated Cron Jobs
**What goes wrong:** A cron job running `arr-oldies clean --delete --execute` hangs indefinitely because `typer.confirm()` waits for input from a non-interactive stdin.  
**Why it happens:** Interactive prompt invoked in headless environment without `--yes`.  
**How to avoid:** Detect non-TTY / non-interactive execution (e.g. `sys.stdin.isatty() is False`). If not interactive and `--yes` is not passed, fail fast with a descriptive error: `Error: Interactive confirmation required. Use --yes for automated / non-interactive execution.`  
**Warning signs:** Cron jobs remaining active in process tables forever.

### Pitfall 4: JSON Output Contaminated by Confirmation Prompts or Spinners
**What goes wrong:** `arr-oldies clean --delete --format json | jq .` fails with JSON parse errors.  
**Why it happens:** Confirmation panels, dry-run banners, or spinner animations were printed to `stdout` instead of `stderr`.  
**How to avoid:** In JSON mode, route all diagnostic, confirmation, and warning messages to `stderr_console`, keeping `stdout` reserved purely for the final JSON payload.  
**Warning signs:** `jq` throws `parse error: Invalid character at line 1`.

---

## Code Examples

### 1. Radarr API Client Extensions (`arr_oldies.api.radarr`)

```python
# [VERIFIED: Radarr v3/v4 REST API specifications]
from arr_oldies.api.base import BaseArrClient
from arr_oldies.constants import RADARR_MOVIE_ENDPOINT, RADARR_MOVIEFILE_ENDPOINT

class RadarrClient(BaseArrClient):
    # (Existing query methods: get_movies, get_movie_files, get_history, etc.)

    async def delete_movie_file(self, movie_file_id: int) -> bool:
        """Delete a specific movie file from disk and Radarr database via API."""
        endpoint = f"{RADARR_MOVIEFILE_ENDPOINT}/{movie_file_id}"
        response = await self.delete(endpoint)
        return response.status_code in (200, 204)

    async def unmonitor_movie(self, movie_id: int) -> bool:
        """Unmonitor a movie in Radarr using the bulk movie editor endpoint."""
        endpoint = f"{RADARR_MOVIE_ENDPOINT}/editor"
        payload = {"movieIds": [movie_id], "monitored": False}
        response = await self.put(endpoint, json=payload)
        return response.status_code in (200, 202)

    async def delete_movie(
        self,
        movie_id: int,
        delete_files: bool = False,
        add_exclusion: bool = False,
    ) -> bool:
        """Remove a movie entry entirely from the Radarr library database."""
        endpoint = f"{RADARR_MOVIE_ENDPOINT}/{movie_id}"
        params = {
            "deleteFiles": str(delete_files).lower(),
            "addImportExclusion": str(add_exclusion).lower(),
        }
        response = await self.delete(endpoint, params=params)
        return response.status_code in (200, 204)
```

---

### 2. Sonarr API Client Extensions (`arr_oldies.api.sonarr`)

```python
# [VERIFIED: Sonarr v3/v4 REST API specifications]
from arr_oldies.api.base import BaseArrClient
from arr_oldies.constants import (
    SONARR_EPISODE_ENDPOINT,
    SONARR_EPISODEFILE_ENDPOINT,
    SONARR_SERIES_ENDPOINT,
)

class SonarrClient(BaseArrClient):
    # (Existing query methods: get_series, get_episode_files, get_episodes, get_history, etc.)

    async def delete_episode_file(self, episode_file_id: int) -> bool:
        """Delete a specific episode file from disk and Sonarr database via API."""
        endpoint = f"{SONARR_EPISODEFILE_ENDPOINT}/{episode_file_id}"
        response = await self.delete(endpoint)
        return response.status_code in (200, 204)

    async def unmonitor_series(self, series_id: int) -> bool:
        """Unmonitor an entire TV series in Sonarr using the series editor endpoint."""
        endpoint = f"{SONARR_SERIES_ENDPOINT}/editor"
        payload = {"seriesIds": [series_id], "monitored": False}
        response = await self.put(endpoint, json=payload)
        return response.status_code in (200, 202)

    async def unmonitor_episodes(self, episode_ids: list[int]) -> bool:
        """Unmonitor specific individual episodes in Sonarr."""
        endpoint = f"{SONARR_EPISODE_ENDPOINT}/monitor"
        payload = {"episodeIds": episode_ids, "monitored": False}
        response = await self.put(endpoint, json=payload)
        return response.status_code in (200, 202)

    async def delete_series(
        self,
        series_id: int,
        delete_files: bool = False,
        add_exclusion: bool = False,
    ) -> bool:
        """Remove a TV series entry entirely from the Sonarr library database."""
        endpoint = f"{SONARR_SERIES_ENDPOINT}/{series_id}"
        params = {
            "deleteFiles": str(delete_files).lower(),
            "addImportListExclusion": str(add_exclusion).lower(),
        }
        response = await self.delete(endpoint, params=params)
        return response.status_code in (200, 204)
```

---

### 3. Action Models & Schemas (`arr_oldies.actions.models`)

```python
# [VERIFIED: Action domain models]
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from pydantic import BaseModel, ConfigDict, Field
from arr_oldies.inventory.models import MediaInventoryItem

class ActionType(StrEnum):
    """Supported mutation actions."""
    DELETE = "delete"
    UNMONITOR = "unmonitor"
    UNMONITOR_EPISODE = "unmonitor_episode"
    REMOVE = "remove"

class ActionItem(BaseModel):
    """An individual media item paired with requested action types."""
    model_config = ConfigDict(extra="ignore")
    item: MediaInventoryItem
    action_types: list[ActionType]

class ActionPlan(BaseModel):
    """Aggregated execution plan detailing all proposed actions."""
    model_config = ConfigDict(extra="ignore")
    target_actions: list[ActionType]
    items: list[ActionItem] = Field(default_factory=list)
    total_items: int = 0
    total_size_bytes: int = 0
    instances_breakdown: dict[str, int] = Field(default_factory=dict)
    dry_run: bool = True

class ActionResult(BaseModel):
    """Result of an action performed on a media item."""
    model_config = ConfigDict(extra="ignore")
    item_id: str
    instance_name: str
    action_type: ActionType
    success: bool
    freed_bytes: int = 0
    error_message: str | None = None

class ExecutionReport(BaseModel):
    """Summary of executed action mutations."""
    model_config = ConfigDict(extra="ignore")
    mode: str = "execute"
    executed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    target_actions: list[ActionType] = Field(default_factory=list)
    total_attempted: int = 0
    successful_count: int = 0
    failed_count: int = 0
    total_freed_bytes: int = 0
    results: list[ActionResult] = Field(default_factory=list)
    duration_seconds: float = 0.0
```

---

### 4. CLI `clean` Command Structure (`arr_oldies.cli`)

```python
# [VERIFIED: Typer CLI command integrating Phase 1-5 capabilities]
@app.command("clean")
def clean_command(
    ctx: typer.Context,
    # Actions (at least one required)
    delete: Annotated[bool, typer.Option("--delete", help="Delete media file(s) via *arr API.")] = False,
    unmonitor: Annotated[bool, typer.Option("--unmonitor", help="Unmonitor movie or entire TV show.")] = False,
    unmonitor_episode: Annotated[bool, typer.Option("--unmonitor-episode", help="Unmonitor specific episode(s).")] = False,
    remove: Annotated[bool, typer.Option("--remove", help="Remove complete movie/series entry from library.")] = False,
    # Safety Guards
    execute: Annotated[bool, typer.Option("--execute", help="Execute write operations (default is dry-run).")] = False,
    yes: Annotated[bool, typer.Option("-y", "--yes", help="Bypass interactive confirmation prompt.")] = False,
    # Targeting & Filtering (shared with scan)
    radarr: Annotated[bool, typer.Option("--radarr", help="Target only Radarr instances.")] = False,
    sonarr: Annotated[bool, typer.Option("--sonarr", help="Target only Sonarr instances.")] = False,
    instance: Annotated[list[str] | None, typer.Option("-i", "--instance", help="Specific instance(s).")] = None,
    # ... filters (media_type, audio_lang, min_size, older_than, etc.)
    limit: Annotated[int | None, typer.Option("-n", "--limit", help="Limit target items to top N.")] = None,
    format: Annotated[OutputFormat, typer.Option("-f", "--format", help="Output format ('table' or 'json').")] = OutputFormat.TABLE,
) -> None:
    """Safely delete files, unmonitor media, or remove library entries across *arr instances."""
    # 1. Validate at least one action flag is passed
    actions: list[ActionType] = []
    if delete:
        actions.append(ActionType.DELETE)
    if unmonitor:
        actions.append(ActionType.UNMONITOR)
    if unmonitor_episode:
        actions.append(ActionType.UNMONITOR_EPISODE)
    if remove:
        actions.append(ActionType.REMOVE)

    if not actions:
        print_error("No action specified. Please provide at least one action flag: --delete, --unmonitor, --unmonitor-episode, --remove")
        raise typer.Exit(code=EXIT_CONFIG_ERROR)

    # 2. Ingest, correlate, filter, and sort items (same as scan)
    # ...
    # 3. Build ActionPlan
    executor = ActionExecutor()
    plan = executor.build_plan(items=target_items, actions=actions, dry_run=not execute)

    # 4. Handle Dry-Run Mode
    if not execute:
        if format == OutputFormat.JSON:
            typer.echo(executor.export_plan_json(plan))
        else:
            render_dry_run_table(plan)
            stdout_console.print(
                "[bold yellow]DRY-RUN MODE:[/] No changes were made. Re-run with [bold cyan]--execute[/bold cyan] to apply mutations."
            )
        raise typer.Exit(code=EXIT_SUCCESS)

    # 5. Handle Interactive Confirmation Guard
    if not yes:
        if not sys.stdin.isatty():
            print_error("Interactive confirmation required in execute mode. Use --yes for automated / non-interactive execution.")
            raise typer.Exit(code=EXIT_PROBE_ERROR)

        confirmed = prompt_confirmation(plan, stdout_console)
        if not confirmed:
            stdout_console.print("[yellow]Operation aborted by user. No changes were made.[/yellow]")
            raise typer.Exit(code=EXIT_SUCCESS)

    # 6. Execute Mutations
    report = asyncio.run(executor.execute_plan(plan, target_instances))

    # 7. Render Execution Summary
    if format == OutputFormat.JSON:
        typer.echo(executor.export_report_json(report))
    else:
        render_execution_report_table(report)
        
    raise typer.Exit(code=EXIT_SUCCESS)
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Direct OS filesystem `rm` | Official Radarr/Sonarr v3/v4 REST API deletion | Modern *arr ecosystem | Prevents database corruption, keeps media indexes in sync, prevents immediate automated re-downloads. |
| Dangerous default execution | Dry-run simulation default with `--execute` gate | Standard CLI security best practice | Eliminates accidental data destruction; safe for interactive exploration. |
| Interactive-only scripts | `--execute --yes` dual-flag automation bypass | Modern CLI ergonomics | Enables reliable headless cron job and CI execution while guarding interactive users. |

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Radarr v3/v4 supports `PUT /api/v3/movie/editor` with `{"movieIds": [...], "monitored": false}` for bulk unmonitoring. | §Standard Stack | Low. Individual `PUT /api/v3/movie/{id}` can be used as a direct fallback. |
| A2 | Sonarr v3/v4 supports `PUT /api/v3/episode/monitor` with `{"episodeIds": [...], "monitored": false}`. | §Standard Stack | Low. Individual episode updates can be used as a direct fallback. |

---

## Open Questions

1. **Handling `--unmonitor-episode` when movies are among the targets:**
   - *What we know:* Radarr movies do not have individual episodes.
   - *Recommendation:* If `--unmonitor-episode` is passed and an item is a Movie, record the episode unmonitor action as skipped or a no-op for that item, while executing other requested actions (like `--delete`) normally.

2. **Deduplication of show unmonitoring across multiple episodes:**
   - *What we know:* A scan might target 20 episodes of the same series with `--unmonitor`.
   - *Recommendation:* `ActionExecutor` should deduplicate series unmonitoring requests by `series_id` per instance, calling `PUT /api/v3/series/editor` once per unique series rather than 20 redundant times.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | Runtime | ✓ | 3.12.3 | — |
| pytest | Test suite | ✓ | 9.1.1 | — |
| respx | Mocking *arr APIs | ✓ | 0.23.1 | — |
| httpx | Async HTTP requests | ✓ | 0.28.1 | — |
| rich | CLI UI & Tables | ✓ | 15.0.0 | — |
| typer | CLI argument parsing | ✓ | 0.15.1 | — |
| pydantic | Data validation | ✓ | 2.13.4 | — |

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.1.1 + pytest-asyncio 1.4.0 + respx 0.23.1 |
| Config file | `pyproject.toml` |
| Quick run command | `.venv/bin/pytest tests/test_action_executor.py -x` |
| Full suite command | `.venv/bin/pytest` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| **ACT-01** | Default dry-run mode prints exact simulation without mutating *arr databases | unit / cli | `.venv/bin/pytest tests/test_cli_clean.py -k test_clean_dry_run_default` | ❌ Wave 0 Gap |
| **ACT-02** | `--delete` calls `DELETE /api/v3/moviefile/{id}` and `DELETE /api/v3/episodefile/{id}` | unit | `.venv/bin/pytest tests/test_radarr_client_actions.py tests/test_sonarr_client_actions.py -k test_delete_file` | ❌ Wave 0 Gap |
| **ACT-03** | `--unmonitor` unmonitors movie or full TV series in *arr | unit | `.venv/bin/pytest tests/test_radarr_client_actions.py tests/test_sonarr_client_actions.py -k test_unmonitor` | ❌ Wave 0 Gap |
| **ACT-04** | `--unmonitor-episode` unmonitors specific episode(s) in Sonarr without unmonitoring series | unit | `.venv/bin/pytest tests/test_sonarr_client_actions.py -k test_unmonitor_episodes` | ❌ Wave 0 Gap |
| **ACT-05** | `--remove` removes movie or TV show entry from *arr library | unit | `.venv/bin/pytest tests/test_radarr_client_actions.py tests/test_sonarr_client_actions.py -k test_remove_entry` | ❌ Wave 0 Gap |
| **ACT-06** | `--execute` prompts with Rich confirmation modal listing target files and freed space | cli | `.venv/bin/pytest tests/test_cli_clean.py -k test_clean_execute_confirmation` | ❌ Wave 0 Gap |
| **ACT-07** | `--yes` with `--execute` bypasses confirmation modal for headless execution | cli | `.venv/bin/pytest tests/test_cli_clean.py -k test_clean_execute_yes_bypass` | ❌ Wave 0 Gap |

### Sampling Rate
- **Per task commit:** `.venv/bin/pytest tests/test_action_executor.py -x`
- **Per wave merge:** `.venv/bin/pytest`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/test_action_models.py` — covers ActionType, ActionPlan, ActionItem, ActionResult, ExecutionReport schemas
- [ ] `tests/test_radarr_client_actions.py` — covers Radarr delete file, unmonitor movie, delete movie endpoints
- [ ] `tests/test_sonarr_client_actions.py` — covers Sonarr delete file, unmonitor series, unmonitor episodes, delete series endpoints
- [ ] `tests/test_action_executor.py` — covers ActionExecutor dry-run planning, execution ordering, and failure recovery
- [ ] `tests/test_confirmation.py` — covers Rich confirmation panel rendering and prompt interaction
- [ ] `tests/test_cli_clean.py` — covers CLI `clean` command end-to-end integration across all action flags and safety guards

---

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---|---|---|
| **V4 Access Control** | Yes | Explicit `--execute` requirement prevents unauthorized or accidental deletion. Credential protection via `SecretStr`. |
| **V5 Input Validation** | Yes | Pydantic v2 validation on CLI arguments, integer IDs, and action enum values. |
| **V6 Cryptography** | No | No custom cryptographic routines used; relies on HTTPS/TLS provided by `httpx`. |

### Known Threat Patterns for Safe Action Engine

| Pattern | STRIDE | Standard Mitigation |
|---|---|---|
| **Accidental Mass File Deletion** | Tampering / Denial of Service | Strict dry-run default (ACT-01), mandatory `--execute` flag (ACT-06), and high-contrast Rich confirmation modal listing affected items and space freed. |
| **Non-Interactive Automated Hang** | Denial of Service | Fast-fail check on non-interactive stdin: require `--yes` when `isatty()` is false. |
| **Race Condition with Auto-Snatch** | Tampering | Execute unmonitor operations before issuing file deletion requests. |
| **Endpoint Injection / URL Tampering** | Tampering | Parameterized path constructions using validated integer IDs (`movie_file_id: int`, `episode_file_id: int`). |

---

## Sources

### Primary (HIGH confidence)
- Radarr API v3/v4 REST Specifications — `/api/v3/moviefile/{id}`, `/api/v3/movie/editor`, `/api/v3/movie/{id}`
- Sonarr API v3/v4 REST Specifications — `/api/v3/episodefile/{id}`, `/api/v3/series/editor`, `/api/v3/episode/monitor`, `/api/v3/series/{id}`
- HTTPX Documentation (`encode/httpx`) — Async HTTP request handling and mock transport testing with `respx`
- Rich Documentation (`Textualize/rich`) — Panels, table styling, and interactive prompts
- Typer Documentation (`fastapi/typer`) — Command options, subcommands, and confirmation prompts

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — Reuses existing verified dependencies in `.venv` (Python 3.12, Typer, Rich, HTTPX, Pydantic v2, Respx)
- Architecture: HIGH — Clean separation between API clients, action engine, confirmation guards, and CLI commands
- Pitfalls: HIGH — Critical *arr pitfalls (re-download races, headless deadlocks, JSON stream purity) thoroughly mapped and mitigated

**Research date:** 2026-08-24  
**Valid until:** 2026-09-24
