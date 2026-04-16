# burr_compare package scaffold

This scaffold refactors a long single-file `burr_compare.py` into a small library.

## Goals
- keep Burr source code untouched
- use Burr parser / metric interfaces as-is
- allow both GT and prediction pre-processing before comparison
- keep a compatibility `burr_compare.py` entrypoint

## Layout
- `burr_compare/runner.py`: top-level orchestration
- `burr_compare/preprocess/json_mapping.py`: prediction + GT JSON pre-processing
- `burr_compare/preprocess/ttl_mapping.py`: GT TTL pre-processing
- `burr_compare/burr_imports.py`: local Burr imports
- `burr_compare/meta.py`: Burr meta compatibility
- `burr_compare/gt_resolution.py`: GT path resolution
- `burr_compare/cli.py`: CLI
- `burr_compare.py`: compatibility shim

## What to migrate from your current file
Move logic from the current long `burr_compare.py` into these places:

1. **Path / meta / GT resolution** -> `gt_resolution.py`, `meta.py`
2. **Prediction JSON canonicalization** -> `preprocess/json_mapping.py`
3. **GT TTL surface normalization** -> `preprocess/ttl_mapping.py`
4. **High-level compare orchestration** -> `runner.py`

## Important note
This scaffold is intentionally conservative. It does not change Burr compare logic.
It only creates places where you can transplant your existing rewrite rules.
