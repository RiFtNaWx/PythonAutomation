# A27-T03 - Tests page scan/trigger honesty + list_tests.source

**Epic:** [EPIC-A27](../epics/EPIC-A27-snippet-pointer-trigger.md)
**PRD:** [PRD-003](../prd/PRD-003-snippet-pointer-trigger.md)
**Status:** implemented 2026-09-15
**Model (implement):** composer-2.5
**Depends on:** A27-T02 wrap trigger RPC (`snippet` / `mode`, no new `imported_*.py`)
**Step:** current: 0 / 4 - not started

## Problem

The Tests page already paints pointer language (`ate/ui/web/index.html` ~371 still also says "Wrap writes a scaffold"; `app.js` `wrapSelectedDetected` ~4660; Setup Test program already renders `t.source.file` ~3712). Worker `list_tests` (`ate/worker/server.py` ~237) does **not** emit `source`. `docs/VIBE_CODE.md` Path C and `AGENTS.md` wrap row still say wrap writes `imported_<id>.py`. `check_ui_contract` only asks HTML to mention pointer/snippet; it does not fail the leftover "scaffold" sentence.

`list_tests.specs` already comes from `load_part_specs` (limits yaml). This ticket must not move specs into `app.js`. It must stop the UI/docs from describing A16 copy as the live wrap path, and must show `src file:line` from the map/registry.

## Acceptance

WHEN `list_tests` returns, THE SYSTEM SHALL include `source: {file, lineno, fn}` for ids present in `snippet_map.yaml` (and MAY fill the same from Path B `inspect` when mapped). THE SYSTEM SHALL keep attaching `specs` from `load_part_specs` and SHALL NOT hardcode test ids or min/max tables in `app.js`.

WHEN the operator opens Tests -> Detect after T01/T02, THE SYSTEM SHALL show unmatched + located snippet rows (already wired to `res.located`) and Remember + enable SHALL call existing `wrap_detected_test` (no new Python write from JS).

WHEN the Tests page hint / UI_CONTRACT / VIBE_CODE Path C / AGENTS.md wrap row describe wrap, THE SYSTEM SHALL say scan remembers + trigger original, SHALL NOT say new wraps write `imported_<id>.py` as the happy path, and SHALL keep leftover-honest mention that `imported_input_off_leakage.py` may still exist from A16.

WHEN an engineer changes a spec max in `ate/config/limits/<key>.yaml` and `list_tests` is called, THE SYSTEM SHALL return the new max on `specs` (already true -- add or extend a check so it cannot regress via UI rewrite).

WHEN `python -m ate.core.check_ui_contract` runs, THE SYSTEM SHALL pass: Tests hint matches pointer+trigger; no hardcoded test-id arrays for the program list in `app.js`; `btn-copy-tests` still absent; A13/A14 still parked.

## Why it is not a one-liner

UI already over-claims trigger. If this ticket only bumps `?v=` without `list_tests.source`, Setup Test program never shows `src file:line`. If docs keep Path C = copy, vibe-coders will keep filling `imported_*.py` and the map will lie. If someone "helps" by listing tests in `app.js`, limits yaml stops being SoT.

## Files to touch

| File | Change |
|------|--------|
| `ate/worker/server.py` | Additive `source` on `list_tests` from snippet map. Do not reshape other keys. |
| `ate/ui/web/index.html` | Tests hint: remove "Wrap writes a scaffold" as the live path. Pointer + trigger. Bump `?v=`. |
| `ate/ui/web/app.js` | Only if `source` paint needs a null-safe tweak. Do not hardcode test lists. Bump `?v=`. |
| `ate/ui/web/UI_CONTRACT.md` | Align item 14 with shipped T02 (already close). |
| `docs/VIBE_CODE.md` | Path C = remember + trigger; leftover A16 copy named. Scaffold file stays an honesty example. |
| `AGENTS.md` | Wrap row: pointer + trigger; do not say new wraps write `imported_*.py` as done. |
| `ate/core/check_ui_contract.py` | Assert hint/contract tokens; forbid hardcoded program-id arrays if that is the trap. |
| `ate/core/check_specs_datalog.py` or `check_add_test.py` | Assert limits yaml change is what `list_tests`/`load_part_specs` returns (no UI table). |

Do **not** touch: `runner.py`; `database.py` path; `wrap_detected_test` logic (T02); leftover scaffold delete; A25 suggest-enable UI; left rail / fonts.

## Checks to run

```
python -m ate.core.check_ui_contract
python -m ate.core.check_add_test
python -m ate.core.check_test_detect
python -m ate.core.check_specs_datalog
```

Tell operator **Ctrl+F5** after UI land. Restart worker if `list_tests` payload changed.

## Out of ticket

- Map persist / vendor AST -> A27-T01
- Wrap trigger / invert wrap-copy checks -> A27-T02
- Named groups (A26); suggest-enable (A25); wizard; Monaco

## Step

current: 0 / 4 - not started

## Agent prompt

> Implement A27-T03 only in `C:\Users\OoiJianHong\Eugene's Repo\PythonAutomation`. Epic: `docs/epics/EPIC-A27-snippet-pointer-trigger.md`. PRD: `docs/prd/PRD-003-snippet-pointer-trigger.md`. Ticket: `docs/tickets/A27-T03-ui-scan-source.md`. Depends on A27-T02 already in tree.
>
> Analog reuse: TAS lane N/A (extend-live). Live files: `ate/worker/server.py` `list_tests`, `ate/ui/web/index.html`, `app.js`, `UI_CONTRACT.md`, `docs/VIBE_CODE.md`, `AGENTS.md`, `check_ui_contract.py`. Do not redesign left rail / fonts. Do not hardcode test lists in `app.js`. Do not edit `runner.py`. Bump `?v=`. Ctrl+F5. No GitHub Issues. No A25/A26. No reopen A16 tickets.
>
> `list_tests` must emit `source` from `snippet_map.yaml`. Tests hint / Path C docs must say remember + trigger, not new wrap-copy. Limits yaml remains spec SoT. Leftover `imported_input_off_leakage.py` may be mentioned as A16 honesty, not deleted.
>
> Done when Acceptance WHENs hold and `check_ui_contract` + `check_add_test` + `check_test_detect` + `check_specs_datalog` exit 0. Tell operator Ctrl+F5.
