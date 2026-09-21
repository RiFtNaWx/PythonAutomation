# EPIC-A27 - Remember snippet pointers and trigger the original function

**PRD:** [PRD-003](../prd/PRD-003-snippet-pointer-trigger.md)
**Status:** implemented 2026-09-15. Mode A tickets T01-T03 landed. Do not reopen A16.
**Do not reopen:** A01-A21. A16 tickets stay **implemented** (leftover: wrap still copies). A13 Excel MCP and A14 xyflow stay parked. No-code wizard stays parked.
**Do not:** edit `runner.py`; edit `database.py` path shape; live-import `Lim` / `Ariff` / `Soo`; delete `imported_input_off_leakage.py`; hardcode test lists in `app.js`.

| Field | Value |
|-------|-------|
| Tier | foundation + boundary + capability + visible Tests surface |
| Repo | this repo (`jian-hong/Python_Automation_JH`) |
| Contract impact | additive (`snippet_map.yaml`; wrap/list RPCs grow fields). New wraps stop writing `imported_*.py`. |
| Depends on | A16 implemented leftover; A03 Path B slot (closed) |
| Blocks | A25 and A26 while in flight (shared `test_detect.py` + Tests page) |
| Appetite | 1 wave |

## Goal

1. Detect scan remembers `file:lineno:fn` in `ate/config/snippet_map.yaml` (AST only, never execute).
2. AST-dirty (`input()`, `Lim` / `Ariff` / `Soo` import) = remember + blocked. No live trigger.
3. Remember + enable on AST-clean = live trigger of the original function. No new `imported_<id>.py`.
4. START/DEMO of that id runs the original function via existing `TestSpec.run` (rehydrate on `load_family`, not `runner.py`).
5. Tests page / Setup Test program scan and show pointers. UI never writes Python bodies.

## Tickets

Mode A filed 2026-09-15 (local files only; no GitHub Issues):

| ID | Ticket file | Status | Seam |
|----|-------------|--------|------|
| A27-T01 | [A27-T01-snippet-map-scan.md](../tickets/A27-T01-snippet-map-scan.md) | READY | `snippet_map.yaml` + scan persist + `located` + vendor AST block. No wrap-copy change. |
| A27-T02 | [A27-T02-wrap-trigger-original.md](../tickets/A27-T02-wrap-trigger-original.md) | READY (blocked on T01) | wrap = remember + trigger; no new `imported_*.py`; rehydrate; invert wrap-copy checks |
| A27-T03 | [A27-T03-ui-scan-source.md](../tickets/A27-T03-ui-scan-source.md) | READY (blocked on T02) | `list_tests.source`; Tests hint honesty; VIBE_CODE / AGENTS Path C; Ctrl+F5 |

Implement order: **T01 then T02 then T03**. Wire then consumer. Do not land T03 in the same agent run as T01.

## Parked (not this epic)

- No-code wizard; Monaco
- A13 / A14
- Users table; copy-between-people
- Live vendor import
- Delete leftover `imported_input_off_leakage.py`
- Reopen A16-T01/T02 as failed
- `runner.py` / `database.py` path

## Checks

```
python -m ate.core.check_test_detect
python -m ate.core.check_add_test
python -m ate.core.check_ui_contract
python -m ate.core.check_family_load
python -m ate.core.check_specs_datalog
```

A green check that still requires wrap to write `imported_*.py` is the old A16 leftover -- T02 must invert that. Do not claim PASS without running the inverted check.

## HUMAN_TEST_GATES (founder only to perform)

- [ ] Tests -> Detect shows `file:line` for a known golden / Path B id
- [ ] Remember on a clean fixture does not create a new `imported_*.py`
- [ ] DEMO/START of that id runs (sim ok); stub text `imported scaffold -- fill body` is not the result
- [ ] Change one max in `ate/config/limits/<part>.yaml`; Setup Test program / `list_tests.specs` shows it
- [ ] Add `def test_*` in the original file; next Detect lists it

## Acceptance

See PRD-003 section 4 (buyer seat).

Literal: "the UI does NOT rewrite the code" = no Python body authored by Wrap/Remember. Scan + trigger by id. Original Path B / yaml / golden function stay SoT.
