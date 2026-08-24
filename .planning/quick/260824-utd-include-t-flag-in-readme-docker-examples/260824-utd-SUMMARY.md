---
quick_id: 260824-utd
slug: include-t-flag-in-readme-docker-examples
description: include -t flag in README docker examples for colored Rich CLI output
status: complete
date: 2026-08-24
---

# Quick Task Summary: Include -t flag in README Docker examples

## Work Done
1. **Docker Quickstart Examples**:
   - Updated `validate-config`, `scan`, `clean` (automated/headless), and custom config path examples to include the `-t` flag (`docker run -t --rm ...`).
   - Kept `-it` on interactive `clean` with clarification that it allocates pseudo-TTY and attaches stdin.
   - Added explanation note in `Volume Mounting & Configuration Discovery` that `-t` allocates a pseudo-TTY so Rich renders styled colored tables and summary cards.
   - Added `tty: true` to the Docker Compose service definition example.
