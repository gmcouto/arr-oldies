# Phase 6: Support Composite Time Formats for Age Filters - Research

## User Constraints

- Support composite/compound time duration expressions in `--older-than` and `--newer-than` CLI options (e.g., `1y1m1d` representing 1 year + 1 month + 1 day = 396 days).
- Must preserve full backward compatibility for existing formats (`30`, `30d`, `6m`, `1y`, `2w`, `90d`, `2years`).
- Must support space-separated, comma-separated, or concatenated units (`1y1m1d`, `1y 1m 1d`, `1 year 1 month 1 day`, `2y6m`).
- Must handle standard time units:
  - Years: `y`, `yr`, `yrs`, `year`, `years` -> 365 days
  - Months: `m`, `mo`, `mos`, `month`, `months` -> 30 days
  - Weeks: `w`, `wk`, `wks`, `week`, `weeks` -> 7 days
  - Days: `d`, `day`, `days`, or bare integer -> 1 day
- Must raise descriptive `ParseError` for invalid tokens, unknown units, or malformed duration strings.

---

## Phase Overview & Requirements

- **Requirement INVT-05**: Filter inventory items by audio language, media type, size bounds, and relative age or date cutoffs.
- **Goal**: Extend the relative age interval parser (`parse_age_cutoff` in `src/arr_oldies/inventory/parser.py`) to parse both single and composite human-friendly time durations into total integer days.

---

## Architecture & Component Analysis

### Source Locations
1. **`src/arr_oldies/inventory/parser.py`**:
   - Contains `parse_age_cutoff(age_str: str) -> int`.
   - Current implementation uses `AGE_REGEX = re.compile(r"^\s*([0-9]+)\s*([a-zA-Z]*)\s*$")`, which only matches a single integer and trailing unit.
   - Calling locations:
     - `src/arr_oldies/cli.py:333, 334`: CLI `scan` command for `--older-than` and `--newer-than`.
     - `src/arr_oldies/cli.py:621, 622`: CLI `clean` command for `--older-than` and `--newer-than`.
2. **`src/arr_oldies/exceptions.py`**:
   - `ParseError(ArrOldiesError)` is caught in `cli.py` and rendered with `print_error()` and exit code `EXIT_CONFIG_ERROR` (2).
3. **`tests/test_parser.py`**:
   - Contains unit tests for `parse_age_cutoff`.
4. **`tests/test_cli_scan.py` & `tests/test_cli_clean.py`**:
   - End-to-end CLI integration tests passing `--older-than` / `--newer-than`.

---

## Implementation Patterns & Algorithms

### Regex Tokenization Algorithm for Composite Durations

To handle both single unit strings (`30d`, `6m`, `90`) and composite strings (`1y1m1d`, `1y 2mo 3d`, `2years, 6months`):

1. **Bare Integer Case**:
   - If input is pure digits `^\s*([0-9]+)\s*$`, return `int(input)` (days).

2. **Composite Token Matching**:
   - Token pattern: `re.compile(r"([0-9]+)\s*([a-zA-Z]+)")`
   - Unit multipliers mapping:
     - Years: `{"y", "yr", "yrs", "year", "years"}: 365`
     - Months: `{"m", "mo", "mos", "month", "months"}: 30`
     - Weeks: `{"w", "wk", "wks", "week", "weeks"}: 7`
     - Days: `{"d", "day", "days"}: 1`
   - Validation against trailing/leftover non-whitespace characters:
     - Strip whitespace and optional commas/delimiters between tokens.
     - Ensure the sum of matched token spans reconstructs the full sanitized string so that unparsed garbage (e.g. `1y2z3d` or `1y1m1d_extra`) is detected and rejected with `ParseError`.

3. **Accumulation**:
   - Total days = sum of (value * multiplier)
   - If no tokens matched or leftover invalid chars remain, raise `ParseError(f"Invalid age specification: '{age_str}'...")`.

---

## Test Coverage & Edge Cases

### Test Matrix
- **Single units**: `30`, `30d`, `2w`, `6m`, `1y`, `2years` (existing tests must continue passing).
- **Composite concatenated**: `1y1m1d` -> 365 + 30 + 1 = 396 days.
- **Composite spaced**: `1y 1m 1d`, `2y 6m`, `3w 4d`.
- **Composite with full words**: `1 year 2 months 3 days`, `2 weeks and 5 days` (or comma separated `1y, 2m, 3d`).
- **Mixed case**: `1Y1M1D`, `2Years 3Months`.
- **Out-of-order units**: `1d 1m 1y` -> 396 days.
- **Multiple same units**: `1y 1y` -> 730 days.
- **Invalid cases**:
  - `bad_age`
  - `1y2x3d` (unknown unit 'x')
  - `1y1m1d extra` (unrecognized trailing tokens)
  - `-5d` (negative values)
  - `""` (empty string)
- **CLI integration**:
  - `scan --older-than 1y1m1d`
  - `clean --older-than 2y6m --dry-run`

---

## Validation Architecture

### Automated Verification Plan
1. **Unit Tests (`tests/test_parser.py`)**:
   - Parametrized tests covering all single and composite unit combinations.
   - Error cases asserting `ParseError` with clear error messages.
2. **CLI Integration Tests (`tests/test_cli_scan.py`, `tests/test_cli_clean.py`)**:
   - Verify `--older-than 1y1m1d` and `--newer-than 6m2w` filter items correctly via Typer `CliRunner`.
3. **Full Test Suite & Linters**:
   - `pytest -v` (ensure all 214+ tests pass).
   - `ruff check .`
   - `mypy src/`
