---
phase: quick
plan: 260824-uaf
type: execute
files_modified:
  - README.md
---

# Quick Plan: Use fixed config path for Docker alias in README

## Objective
Update the shell alias and wrapper function examples in `README.md` to use a fixed path (such as `$HOME/.config/arr-oldies/config.yaml` or an explicit absolute path) rather than `$(pwd)/config.yaml`, ensuring the alias works from any working directory.

## Tasks

### Task 1: Update README.md alias documentation
- Update Option B in `README.md` to use a fixed config path `$HOME/.config/arr-oldies/config.yaml` or `/path/to/config.yaml`.
- Include both shell alias and shell function examples for users.
