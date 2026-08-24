---
phase: quick
plan: 260824-ucl
type: execute
files_modified:
  - README.md
---

# Quick Plan: Add Docker CLI / Interactive Shell Modes to README

## Objective
Update `README.md` to document interactive container shell (`sh`) and shell alias usage patterns for Docker, allowing users to run `arr-oldies` repeatedly without repeating the `docker run` prefix.

## Tasks

### Task 1: Update README.md with Docker interactive CLI mode instructions
- Add "Interactive CLI Mode & Shell Aliases" subsection under Docker Quickstart in `README.md`.
- Document dropping into container shell (`docker run -it ... sh`) and running `arr-oldies` commands sequentially.
- Document creating a shell alias (`alias arr-oldies="docker run -it --rm ..."`) for native CLI execution.
