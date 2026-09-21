---
keywords: snippet-map, pointer, trigger, wrap, detect, imported-scaffold, leftover-honest, path-c, ast-clean, lim-ariff-soo, prd-003, a27, remember
main_idea: UI scans and triggers original file:line. Wrap no longer writes imported_*.py. snippet_map.yaml + load_family rehydrate. Limits/params stay in original yaml.
---

PREFLIGHT: PARTIAL
reuse: `docs/subagents_findings/2026-09-15_snippet-pointer-trigger.md`, A16 leftover wrap-copy, Path B/C
spawn: prd-agent + UI lane; parent implemented T01-T03 Python

## Working conversion

- `list_detected_tests` writes `ate/config/snippet_map.yaml` and returns `detected` + `located`.
- AST-block `input()` and `Lim`/`Ariff`/`Soo` (never execute at scan).
- `wrap_detected_test` remembers + live-triggers the original function. No new `imported_<id>.py`.
- `registry.load_family` rehydrates live pointers.
- `list_tests.source` prefers the map, else inspect.
- Tests page Remember + enable; Test program shows `src file:line`.

## Leftover

`ate/tests/logic/imported_input_off_leakage.py` still exists from A16. Do not delete. Do not DEMO it as done.

## Checks

```
python -m ate.core.check_test_detect
python -m ate.core.check_add_test
python -m ate.core.check_ui_contract
python -m ate.core.check_family_load
```
