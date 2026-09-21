# A22-T01 - Assign product codes + ensure this operator folders

**Epic:** [EPIC-A22](../epics/EPIC-A22-operator-assign-folders.md)
**PRD:** [PRD-002](../prd/PRD-002-operator-profile-workflow.md)
**Status:** implemented
**Model (implement):** composer-2.5
**Depends on:** A15 path (shipped). No UI required for this ticket.
**Blocks:** A22-T02 (UI calls this RPC)
**Step:** current: 4 / 4 - done (check_assign_owner + operator_tree + new_product exit 0)

## Problem

Setup Save person only upserts `owners.yaml` for the **on-screen** SKU and tells the operator to Apply campaign (`ate/ui/web/app.js` `savePersonFromSetup` ~2645-2667; hint: "Apply campaign to create folders"). There is no core/RPC that:

1. Takes a person label + a list of product codes,
2. Matches each code to inventory / part yaml,
3. Upserts `parts:` and `ensure_product` Version_1 for **that** operator only,
4. Reports unmatched codes without scraping en.run-ic.com.

`upsert_owner` (`ate/core/database.py` ~593-666) appends `parts:` but never calls `ensure_product`. `ensure_product` (`ate/core/new_product.py` ~548+) already creates `#Test_Database/{Component}/{Part}/{Package}/{Operator}/Version_1/` and must not be reshaped. Unassign cannot use append-only `upsert_owner` today -- dropping a `parts:` entry needs an explicit remove path that does not delete folders.

## Acceptance

WHEN the worker receives an assign call for a real person (not All / Kevin) with product codes that match inventory or `ate/config/parts/<key>.yaml`, THE SYSTEM SHALL upsert that person in `owners.yaml` with those codes on `parts:` and SHALL create `#Test_Database/{Component}/{Part}/{Package}/{ThatLabel}/Version_1/` for each matched SKU via `ensure_product`, and SHALL NOT copy or move another operator's `workbook/` or `sessions/`.

WHEN a product code does not match inventory or part yaml, THE SYSTEM SHALL return it in an unmatched list and SHALL NOT scrape en.run-ic.com and SHALL NOT invent a campaign folder for that code.

WHEN the assign call asks to unassign a matched code (drop from `parts:`), THE SYSTEM SHALL remove that entry from `owners.yaml` `parts:` and SHALL NOT delete Version folders on disk.

WHEN operator is All or Kevin (or observer), THE SYSTEM SHALL refuse the write.

WHEN `python -m ate.core.check_assign_owner` runs (or an extended `check_new_product` block named in the check module docstring), THE SYSTEM SHALL pass: Jane + RS1G08 (or equivalent temp label) creates a sibling tree and SHALL NOT clobber an existing sibling operator's tree under the same Component/Part/Package.

## Why it is not a one-liner

"Migrate related products to him" reads like MOVE. The trap is copying Ariff/ChangThong/Eugene `workbook/` or `sessions/` into the new person. Literal migrate here = upsert `parts:` + `ensure_product` for **this** operator Version_1 only. Second trap: inventing a Users table or changing `DbContext.root()` path shape. Third: unmatched codes must surface, not be scraped from en.run-ic.com. Fourth: `upsert_owner` only appends `parts:` -- unassign needs a remove-from-parts helper without folder delete.

## Files to touch

| File | Change |
|------|--------|
| `ate/core/database.py` | Assign/unassign helpers on `parts:` (reuse `upsert_owner` / add drop-parts). Refuse All/Kevin. Never delete folders. |
| `ate/core/new_product.py` | Call `ensure_product` per matched code (component/package from inventory / part yaml). Do not change path shape. Reuse `_inventory_match` / `part_key_for`. |
| `ate/worker/server.py` | One additive RPC (e.g. `assign_owner_products`) that returns `{owner, ensured[], unmatched[], action}`. Thin wrapper only. |
| `ate/core/check_assign_owner.py` (preferred) **or** extend `ate/core/check_new_product.py` | One runnable check: matched ensure + unmatched report + sibling non-clobber + All refuse. No test framework. |

Do **not** touch: `DbContext.root()` shape; UI (`app.js` / `index.html` -- that is T02); A23 Forget passphrase; A13/A14; Users table; scrape paths.

## Checks to run

```
python -m ate.core.check_assign_owner
python -m ate.core.check_operator_tree
python -m ate.core.check_new_product
```

(If the assign assertions live inside `check_new_product` instead, document that in the check docstring and run that module; still run `check_operator_tree`.)

Idle-restart worker after RPC lands (`restart_ate_worker.bat` when idle). No Ctrl+F5 required for this ticket alone.

## Out of ticket

- Setup product-code picker / unassign UI / `?v=` bump -> A22-T02
- Typed-phrase Forget -> A23 (do not cut)
- Limits overlay / suggest-import / named groups -> A24-A26 (do not cut)
- Folder delete; Users table; A13/A14; reopen A01-A21

## Step

current: 0 / 4 - not started

## Agent prompt

> Implement A22-T01 only in `C:\Users\OoiJianHong\Eugene's Repo\PythonAutomation`. Epic: `docs/epics/EPIC-A22-operator-assign-folders.md`. PRD: `docs/prd/PRD-002-operator-profile-workflow.md`. Ticket: `docs/tickets/A22-T01-assign-ensure-unmatched.md`.
>
> Analog reuse: TAS lane N/A (extend-live console). Live files: `ate/core/database.py`, `ate/core/new_product.py`, `ate/worker/server.py`, new or extended check under `ate/core/`. Analog read-only: `docs/subagents_findings/2026-09-11_scale-operator-tree.md`, `2026-09-11_codeless-owner-tags.md`, `2026-09-14_operator-profile-workflow.md`. Do not redesign UI tokens/layout. DISTILL the analog segment into original Netie code in the live product. Analog clones stay frozen.
>
> Add one RPC + core path: person label + product codes -> match inventory/part yaml -> upsert `owners.yaml` `parts:` -> `ensure_product` Version_1 for **this** operator only -> return unmatched. Unassign = drop `parts:` entry; folders stay. Refuse All/Kevin. Do not copy/move another operator's workbook/sessions. Do not change `DbContext.root()`. Do not scrape en.run-ic.com. No UI. No A23-A26. No GitHub Issues. No reopen A01-A21. A13/A14 parked.
>
> Done when the Acceptance WHENs hold and `python -m ate.core.check_assign_owner` (or documented `check_new_product` block) + `check_operator_tree` + `check_new_product` exit 0. Idle-restart worker if RPC changed.
