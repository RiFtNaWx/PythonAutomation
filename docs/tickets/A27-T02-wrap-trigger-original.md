# A27-T02 - Wrap remembers and triggers the original function

**Epic:** [EPIC-A27](../epics/EPIC-A27-snippet-pointer-trigger.md)
**PRD:** [PRD-003](../prd/PRD-003-snippet-pointer-trigger.md)
**Status:** implemented 2026-09-15
**Model (implement):** composer-2.5
**Depends on:** A27-T01 (`snippet_map.yaml` + `located` + vendor AST block)
**Blocks:** A27-T03
**Step:** current: 0 / 4 - not started

## Problem

`wrap_detected_test` (`ate/core/test_detect.py` ~432-591) still writes `ate/tests/<family>/imported_<id>.py` with a stub `run()` that returns `imported scaffold -- fill body` and never calls the golden function. Source is a comment ("reference only, not imported at runtime"). Return dict is `{ok, id, family, module, ...}` -- no `snippet` / `mode`. UI `wrapSelectedDetected` already expects `res.snippet` and `res.mode`.

`check_test_detect` asserts that wrap creates `imported_detect_probe.py`. `check_add_test` requires wrap to write an imported scaffold and the wrap docstring to mention `imported_`. Those checks freeze the A16 leftover.

START already runs `TestSpec.run` from the registry (`load_family`). If wrap does not register a trigger at the original `file:fn`, DEMO of a "Remembered" id either is missing or runs the stub. Founder: UI does not rewrite the code; it triggers the original section. Do not edit `runner.py`.

## Acceptance

WHEN `wrap_detected_test` succeeds for an AST-clean function, THE SYSTEM SHALL persist/update the snippet pointer, SHALL register a `TestSpec` whose `run()` calls that original function, SHALL return `{ok, id, family, snippet: {file, lineno, fn}, mode: "trigger", ...}`, SHALL enable the id on this Version catalog when `enable_part` is set (existing `enable_tests_on_part`, default not shared part yaml), and SHALL NOT write a new `imported_<id>.py` and SHALL NOT rewrite the original file.

WHEN the function or file is AST-dirty (`input()` or `Lim`/`Ariff`/`Soo` import), THE SYSTEM SHALL refuse live trigger (ValueError naming the reason), SHALL still leave/keep the remembered blocked pointer from T01, and SHALL NOT import vendor packages.

WHEN `load_family` runs after worker restart, THE SYSTEM SHALL rehydrate live-trigger specs from `snippet_map.yaml` for AST-clean pointers (hook from `registry.load_family` or `test_detect`, not `runner.py`) so START/DEMO of that id still works without the A16 module file.

WHEN a check calls the registered spec `run()` on the clean detect_probe fixture (sim instr ok), THE SYSTEM SHALL return the original function's result (fixture `{"ok": True, ...}`), not `imported scaffold -- fill body`.

WHEN `python -m ate.core.check_test_detect` runs, THE SYSTEM SHALL pass: after clean wrap, `imported_detect_probe.py` must **not** exist; map has the pointer; registry has the id; dirty wrap still raises.

WHEN `python -m ate.core.check_add_test` runs, THE SYSTEM SHALL pass **without** requiring wrap to write a new scaffold. Leftover `imported_input_off_leakage.py` MAY remain on disk with its fill-body marker (do not delete). Path B `eugene_cap.py` / cin/cpd rules stay.

## Why it is not a one-liner

Deleting the write without a rehydrate hook means the id vanishes after restart. Importing the golden at wrap time without a fresh AST check would execute `Lim.*` (BAN). Generating one helper per id is the old copy. Touching `runner.py` to special-case snippet ids is the blast-radius miss. Inverting checks without keeping leftover-honest `imported_input_off_leakage.py` pretends A16 never shipped.

## Files to touch

| File | Change |
|------|--------|
| `ate/core/test_detect.py` | `wrap_detected_test`: remember + register trigger helper; no new `imported_*.py`; return `snippet`/`mode`. |
| `ate/core/registry.py` | Optional one-call rehydrate at end of `load_family`. Do not change `FAMILY_PACKAGES`. |
| `ate/worker/server.py` | Thin: pass through wrap result (already). Do not add a second wrap path. |
| `ate/core/check_test_detect.py` | Invert: clean wrap must **not** create `imported_detect_probe.py`; assert trigger result + map. |
| `ate/core/check_add_test.py` | Stop requiring wrap to write scaffold / docstring `imported_`. Keep leftover file as honesty if still present. Keep Path B cin/cpd. |

Do **not** touch: `runner.py`; `database.py` path; UI (T03); delete leftover `imported_input_off_leakage.py`; A13/A14; vendor trees as runtime imports.

## Checks to run

```
python -m ate.core.check_test_detect
python -m ate.core.check_add_test
python -m ate.core.check_family_load
```

Idle-restart worker after wrap/rehydrate lands (`restart_ate_worker.bat` when idle).

## Out of ticket

- Scan map / `located` / vendor AST (must already be T01)
- Tests hint + `list_tests.source` + VIBE_CODE / AGENTS Path C -> A27-T03
- Monaco; wizard; delete leftover scaffold

## Step

current: 0 / 4 - not started

## Agent prompt

> Implement A27-T02 only in `C:\Users\OoiJianHong\Eugene's Repo\PythonAutomation`. Epic: `docs/epics/EPIC-A27-snippet-pointer-trigger.md`. PRD: `docs/prd/PRD-003-snippet-pointer-trigger.md`. Ticket: `docs/tickets/A27-T02-wrap-trigger-original.md`. Depends on A27-T01 already in tree.
>
> Analog reuse: TAS lane N/A (extend-live). Not TAS-POINTER. Live files: `ate/core/test_detect.py` wrap, optional `registry.load_family` rehydrate, `check_test_detect.py`, `check_add_test.py`. BAN executing `Lim.*` / `Ariff.*` / `Soo.*`. Do not edit `runner.py` or `database.py` path. Do not delete `ate/tests/logic/imported_input_off_leakage.py`. No UI (T03). No GitHub Issues. No reopen A16 tickets.
>
> Wrap of a clean golden must remember + live-trigger the original function, return `snippet`/`mode`, and must not write `imported_<id>.py`. Dirty stays refused. Rehydrate on family load from `snippet_map.yaml`. Invert wrap-copy checks. Path B cin/cpd stays.
>
> Done when Acceptance WHENs hold and `check_test_detect` + `check_add_test` + `check_family_load` exit 0. Idle-restart worker.
