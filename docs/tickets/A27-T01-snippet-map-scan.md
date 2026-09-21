# A27-T01 - Snippet map + Detect scan remembers file:line

**Epic:** [EPIC-A27](../epics/EPIC-A27-snippet-pointer-trigger.md)
**PRD:** [PRD-003](../prd/PRD-003-snippet-pointer-trigger.md)
**Status:** implemented 2026-09-15
**Model (implement):** composer-2.5
**Depends on:** A16 Detect RPC (shipped leftover). No wrap-trigger in this ticket.
**Blocks:** A27-T02
**Step:** current: 0 / 4 - not started

## Problem

Detect already AST-scans `def test_*` and returns `file` + `lineno` on unmatched rows (`ate/core/test_detect.py` `scan_file` ~301, `list_detected_tests` ~348). It does **not** persist a pointer map. It skips already-registered ids, so the UI's `res.located` (`app.js` ~3551) is always empty. `_blocked_reason` (~274) flags `input()` only -- a golden that `import Lim` / `Ariff` / `Soo` can still look wrap-ready. `ate/config/snippet_map.yaml` does not exist.

Without a remembered map, later wrap/START cannot trigger "the snippet section where it is located". This ticket is the foundation only: remember + list. Wrap still copies until T02 (leftover-honest).

## Acceptance

WHEN `list_detected_tests` runs, THE SYSTEM SHALL AST-scan golden roots + `ate/tests` without executing those files, SHALL write/update `ate/config/snippet_map.yaml` with `id -> file, lineno, fn, family, ast_clean, blocked_reason`, SHALL return unmatched rows in `detected`, and SHALL return already-registered / remembered rows in `located` (with `matched: true` and `file:lineno:fn`).

WHEN a scanned file imports `Lim` or `Ariff` or `Soo` (AST `Import` / `ImportFrom`, including `from Lim import ...`), THE SYSTEM SHALL mark every `def test_*` in that file blocked and SHALL still remember the pointer, and SHALL NOT import that module.

WHEN a function contains `input()` (direct or via a helper already covered), THE SYSTEM SHALL keep today's blocked remember behavior.

WHEN an engineer adds a new `def test_*` to a scanned file (check fixture is enough), THE SYSTEM SHALL include it on the next `list_detected_tests`.

WHEN `python -m ate.core.check_test_detect` runs, THE SYSTEM SHALL pass the new map/`located`/vendor-import cases **and** SHALL keep today's dirty-`input()` cases. Wrap-copy of a clean fixture may still write `imported_*.py` in this ticket (T02 inverts that).

## Why it is not a one-liner

Persisting every scan into yaml is the SoT the UI will trust. If scan executed goldens, vendor `Lim.*` would run at Detect time (BAN). If `located` stays missing, the Tests page keeps painting a lie. If vendor imports are not AST-blocked, T02 would live-trigger Ariff trees. Do not change `wrap_detected_test` in this ticket -- that is T02, same file, sequential.

## Files to touch

| File | Change |
|------|--------|
| `ate/config/snippet_map.yaml` | New map (id -> file/lineno/fn/family/ast_clean/blocked_reason). Keep it boring yaml. |
| `ate/core/test_detect.py` | Persist on `list_detected_tests`. Return `located`. AST-block vendor imports at file level. Do **not** change wrap-copy yet. |
| `ate/core/check_test_detect.py` | Assert map written; `located` present; vendor-import fixture blocked+remembered; new `def test_*` appears on rescan. Keep input() cases. |

Do **not** touch: `wrap_detected_test` body (T02); `runner.py`; `database.py` path; UI (`app.js` / `index.html` -- T03); leftover `imported_input_off_leakage.py`; A13/A14; A25/A26.

## Checks to run

```
python -m ate.core.check_test_detect
python -m ate.core.check_family_load
```

Idle-restart worker after RPC payload grows (`located` / map) when idle. No Ctrl+F5 required for this ticket alone (UI already reads `located`).

## Out of ticket

- Wrap stops writing `imported_*.py` / live trigger -> A27-T02
- `list_tests.source` + hint honesty + VIBE_CODE -> A27-T03
- Delete leftover scaffold; Monaco; wizard; `runner.py`

## Step

current: 0 / 4 - not started

## Agent prompt

> Implement A27-T01 only in `C:\Users\OoiJianHong\Eugene's Repo\PythonAutomation`. Epic: `docs/epics/EPIC-A27-snippet-pointer-trigger.md`. PRD: `docs/prd/PRD-003-snippet-pointer-trigger.md`. Ticket: `docs/tickets/A27-T01-snippet-map-scan.md`.
>
> Analog reuse: TAS lane N/A (extend-live console). Not TAS-POINTER. Live files: `ate/core/test_detect.py`, new `ate/config/snippet_map.yaml`, `ate/core/check_test_detect.py`. Analog read-only: `docs/subagents_findings/2026-09-08_f23-detect-wrap-copy-version.md`, `2026-09-13_vibe-code-add-test-tickets.md`. Do not redesign UI tokens/layout. BAN n8n / Monaco / executing `Lim.*` at scan time.
>
> Detect scan must persist `file:lineno:fn` to `snippet_map.yaml` and return `detected` + `located`. AST-only. Block `input()` and `Lim`/`Ariff`/`Soo` imports. Do not change `wrap_detected_test`. Do not edit `runner.py` or `database.py` path. No UI. No T02/T03. No GitHub Issues. No reopen A16 tickets. A13/A14 parked.
>
> Done when the Acceptance WHENs hold and `python -m ate.core.check_test_detect` + `check_family_load` exit 0. Idle-restart worker if RPC payload changed.
