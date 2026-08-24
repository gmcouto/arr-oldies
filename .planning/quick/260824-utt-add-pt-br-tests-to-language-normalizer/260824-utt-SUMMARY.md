---
quick_id: 260824-utt
slug: add-pt-br-tests-to-language-normalizer
description: add explicit pt-br and Portuguese tests to language normalizer test suite
status: complete
date: 2026-08-24
---

# Quick Task Summary: Add pt-br and Portuguese tests to language normalizer

## Work Done
1. **Language Normalizer Tests**:
   - Added parameterized tests in `tests/test_language_normalizer.py` verifying that `pt-br`, `pt`, `por`, `portugues`, and `portuguese` match `Portuguese` audio tracks, and negative matching for mismatched languages.
   - All 256 test suite tests pass.
