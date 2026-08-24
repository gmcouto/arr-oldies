---
quick_id: 260824-uaf
slug: use-fixed-path-for-docker-alias-in-readme
description: update Docker shell alias and function to use fixed config path in README
status: complete
date: 2026-08-24
---

# Quick Task Summary: Use fixed config path for Docker alias in README

## Work Done
1. **Shell Alias & Function Documentation**:
   - Updated Option B in `README.md` to reference a fixed configuration file path (`$HOME/.config/arr-oldies/config.yaml` or an explicit absolute path) rather than `$(pwd)/config.yaml`.
   - Added a shell function example `arr-oldies()` alongside the alias so users can invoke the CLI from any working directory on their host system.
