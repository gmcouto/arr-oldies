---
phase: quick
plan: 260824-utt
type: execute
files_modified:
  - tests/test_language_normalizer.py
---

# Quick Plan: Add pt-br and Portuguese tests to language normalizer

## Objective
Add explicit parameterized test cases for `pt-br`, `pt`, `por`, `portugues`, and `Portuguese` in `tests/test_language_normalizer.py` to test and guarantee Portuguese (Brazilian) lookup and filtering.

## Tasks

### Task 1: Add Portuguese test cases to test_language_normalizer.py
- Add test assertions for `pt-br`, `pt`, `por`, and `portugues` against `["Portuguese"]`.
- Run pytest to verify all test cases pass.
