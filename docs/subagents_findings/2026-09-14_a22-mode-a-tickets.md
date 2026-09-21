---
keywords: a22, mode-a, tickets, assign-owner, ensure-product, unmatched, parts-yaml, setup-picker, unassign, prd-002
main_idea: EPIC-A22 Mode A filed two READY local tickets (T01 core/RPC assign+ensure+unmatched+unassign; T02 Setup picker). Implement T01 then T02. migrate = parts upsert + this-operator ensure_product only.
---

# 2026-09-14 A22 Mode A tickets

PREFLIGHT: PARTIAL
reuse: docs/subagents_findings/2026-09-11_scale-operator-tree.md, 2026-09-11_codeless-owner-tags.md, 2026-09-13_campaign-tests-page.md, 2026-09-14_operator-profile-workflow.md
spawn: skip (epic-agent Mode A; no research flock)

## Filed

| ID | Path | Status |
|----|------|--------|
| A22-T01 | `docs/tickets/A22-T01-assign-ensure-unmatched.md` | READY |
| A22-T02 | `docs/tickets/A22-T02-setup-product-code-picker.md` | READY |

## Acceptance one-liners

- **T01:** Assign matched codes -> `owners.yaml` `parts:` + `ensure_product` this operator Version_1 only; unmatched reported; unassign drops `parts:` (folders stay); All/Kevin refuse; Jane does not clobber Ariff.
- **T02:** Setup multi-code picker + unassign calls T01 RPC; Ctrl+F5 / `?v=` + `check_ui_contract`; no Forget passphrase (A23).

## Implement order

1. A22-T01 (core + RPC + `check_assign_owner`)
2. A22-T02 (Setup UI)

## Hard rules kept

- No GitHub Issues; no code this turn
- No A23-A26 tickets; no reopen A01-A21; A13/A14 parked
- No Users table; no `DbContext.root()` reshape
- migrate != MOVE of another operator's workbook/sessions
- Unmatched = report; do not scrape en.run-ic.com

## Ledger updates

- `docs/epics/EPIC-A22-operator-assign-folders.md` ticket table -> filed READY
- `docs/tickets/INDEX.md` A22-T01/T02 rows + epic note
