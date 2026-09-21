---
keywords: ingest-goldens, goldens, ariff, see-lin, eugene, logic_tests, original, delay, main.py, leftover-honest
main_idea: Byte-copy author trees into goldens/ (do not rewrite delay/timing or paste into ate/tests). INDEX is AST-only. Standalone run is that tree's main.py.
---

## What landed

- `python -m ate.core.ingest_goldens` copies Downloads `logic_tests.py` / `logic_test.py`, Ariff `LabAutomation_v1 - Copy`, See Lin Repo, Eugene `LabAutomation-1` into `goldens/`.
- Skip `venv`, `.git`, `Github_Auto`, non text suffixes. Overwrite dest dir on refresh.
- `goldens/INDEX.md` lists every `def test_*` with `file:line` + first docstring line.
- `goldens/GUIDE.md` + `goldens/templates/test_slot.py` is the add-test recipe in the original `test_parameter()` shape.
- `ate/config/golden_roots.yaml` prefers in-repo `goldens/` first. Detect/Path C scans those; it does not rewrite them.

## Checks that actually ran

- `python -m ate.core.ingest_goldens` -- copied all five sources, INDEX rows=96
- `python -m ate.core.check_ingest_goldens` -- OK
- `python -m ate.core.check_test_detect` -- OK

## Leftover-honest

- `goldens/downloads/logic_test.py` is the RS0204 dispatcher stub (no live `test_*`). Keep as reference; do not treat as a body.
- Vendor `input()` / `Lim.*` / `Ariff.*` / `Soo.*` still blocked for live trigger. Path B in `ate/tests/` for those.
- Do not delete `ate/tests/logic/imported_input_off_leakage.py` (A16 leftover).
- External LabAutomation-1 / 14.7 roots remain in `golden_roots.yaml` as fallback if those folders exist.
- Standalone `python main.py` still needs that tree's `*_setup.py` / instruments on the bench. The ATE console is a separate runtime.
