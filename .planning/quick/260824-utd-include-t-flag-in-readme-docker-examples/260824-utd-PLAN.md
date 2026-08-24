---
phase: quick
plan: 260824-utd
type: execute
files_modified:
  - README.md
---

# Quick Plan: Include -t flag in README Docker examples

## Objective
Update the Docker CLI examples in `README.md` to include the `-t` flag (allocating a pseudo-TTY) so that Rich formatting renders with colored terminal output and tables, and note the use of `-t` and `tty: true` for Docker Compose.

## Tasks

### Task 1: Update README.md Docker examples and notes
- Update the Docker run examples in `README.md` to include `-t` (or `-it` for interactive commands).
- Add a tip note explaining that `-t` allocates a pseudo-TTY for colored formatting and Rich UI tables.
- Add `tty: true` to the Docker Compose example.
