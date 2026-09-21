# A22-T02 - Setup product-code picker + unassign + Ctrl+F5

**Epic:** [EPIC-A22](../epics/EPIC-A22-operator-assign-folders.md)
**PRD:** [PRD-002](../prd/PRD-002-operator-profile-workflow.md)
**Status:** implemented
**Model (implement):** composer-2.5
**Depends on:** A22-T01 RPC (`assign_owner_products` or equivalent)
**Step:** current: 4 / 4 - done (check_ui_contract + assign_owner + operator_tree; worker restarted; Ctrl+F5)

## Problem

Buyer seat needs: type Jane, pick existing SKUs (example RS1G08 + RS1G07), Save, see Jane/Version_1 folders appear beside Ariff without Apply-only for each code. Today `savePersonFromSetup` (`ate/ui/web/app.js` ~2645) only saves the current campaign SKU and leaves `person-hint` saying Apply to create folders (`index.html` `#person-hint` ~137). There is no multi-code picker, no unassign control that drops `parts:` only, and no UI_CONTRACT assert that the new surface stays inside Setup (not a Users page).

Forget passphrase stays A23 -- do not dual-write Forget UI in this ticket.

## Acceptance

WHEN the operator (not All / Kevin) types a person label, selects one or more existing product codes on Setup, and saves assign, THE SYSTEM SHALL call the A22-T01 RPC and SHALL refresh owners / hint so matched codes are on `parts:` and this person's Version_1 trees exist for those SKUs, and SHALL show unmatched codes if any without inventing folders.

WHEN the operator unassigns a product code on that person's Setup profile surface, THE SYSTEM SHALL call the unassign path (drop `parts:` entry) and SHALL NOT delete Version folders, and SHALL update the hint / picker to match yaml.

WHEN operator is All or Kevin, THE SYSTEM SHALL refuse the write in the UI (same gate as `requireWriteOperator` / existing All view-only).

WHEN static UI changes land, THE SYSTEM SHALL bump cache-bust `?v=` on touched `app.js` / `styles.css` / `index.html` per `UI_CONTRACT.md`, and `python -m ate.core.check_ui_contract` SHALL pass (Save person / assign surface stays in Setup; no Users table chrome; `btn-copy-tests` stays absent; A13/A14 stay parked).

## Why it is not a one-liner

Wiring Save person to pass `parts: [current]` without a multi-picker still leaves the Apply loop. Unassign must not call Forget or delete folders. Same Setup person panel is also A23's home -- this ticket must not add typed-phrase Forget or fight A23. Do not redesign left rail / fonts / tab chrome.

## Files to touch

| File | Change |
|------|--------|
| `ate/ui/web/index.html` | Product-code picker + unassign control near Save person / person-hint. Stay inside Setup (`setup-more`). No Users page. |
| `ate/ui/web/app.js` | Call A22-T01 RPC on assign/unassign; refresh owners; report unmatched; keep All/Kevin refuse. Do not implement Forget passphrase (A23). |
| `ate/ui/web/styles.css` | Minimal if needed; follow UI_CONTRACT; no new framework. |
| `ate/ui/web/UI_CONTRACT.md` | Note assign/unassign surface if contract text requires it. |
| `ate/core/check_ui_contract.py` | Assert picker / unassign ids or data-contract hooks exist; Save person still in setup-more; no Users chrome; copy-from-part still parked. |

Bump `?v=` on script/link tags touched.

Do **not** touch: T01 core unless a one-line RPC param fix is required; `DbContext.root()`; A23 Forget; A24-A26; A13/A14.

## Checks to run

```
python -m ate.core.check_ui_contract
python -m ate.core.check_assign_owner
python -m ate.core.check_operator_tree
```

Tell operator **Ctrl+F5** after UI land. Restart worker only if T01 RPC was missing and must be restarted from T01.

## Out of ticket

- Assign/ensure core + unmatched RPC -> A22-T01 (must land first)
- Typed-phrase Forget -> A23
- Limits / suggest-import / groups -> A24-A26
- Folder delete; Users table; scrape; reopen A01-A21

## Step

current: 0 / 4 - not started

## Agent prompt

> Implement A22-T02 only in `C:\Users\OoiJianHong\Eugene's Repo\PythonAutomation`. Epic: `docs/epics/EPIC-A22-operator-assign-folders.md`. PRD: `docs/prd/PRD-002-operator-profile-workflow.md`. Ticket: `docs/tickets/A22-T02-setup-product-code-picker.md`. Depends on A22-T01 RPC already in tree.
>
> Analog reuse: TAS lane N/A (extend-live console). Live files: `ate/ui/web/index.html`, `ate/ui/web/app.js`, `ate/ui/web/styles.css`, `ate/ui/web/UI_CONTRACT.md`, `ate/core/check_ui_contract.py`. Analog read-only: `docs/subagents_findings/2026-09-11_codeless-owner-tags.md`, `2026-09-13_campaign-tests-page.md`, `2026-09-14_operator-profile-workflow.md`, A22-T01 ticket. Do not redesign UI tokens/layout. DISTILL the analog segment into original Netie code in the live product. Analog clones stay frozen.
>
> Add Setup product-code picker + unassign that call A22-T01 RPC. Matched codes -> parts + this operator Version_1. Unmatched reported. Unassign drops `parts:` only; folders stay. Refuse All/Kevin. Bump `?v=`. Extend `check_ui_contract`. Do not add Forget passphrase (A23). Do not touch `DbContext.root()`. No Users table. No A24-A26. No GitHub Issues. No reopen A01-A21. A13/A14 parked. No left-rail / font rewrite.
>
> Done when Acceptance WHENs hold and `check_ui_contract` + `check_assign_owner` + `check_operator_tree` exit 0. Tell operator Ctrl+F5.
