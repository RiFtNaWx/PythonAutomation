---
keywords: a22, assign-owner-products, person-sku, ensure-product, unassign, owners-yaml, prd-002
main_idea: A22 shipped. Save person with product-code chips upserts owners.yaml parts and ensure_product for this operator only. Unassign is yaml-only. Next is A23 FORGET phrase, then A24-A26.
---

# 2026-09-14 A22 assign SKUs + folders (implemented)

PREFLIGHT: PARTIAL
reuse: 2026-09-14_operator-profile-workflow.md, 2026-09-14_a22-mode-a-tickets.md, scale-operator-tree, codeless-owner-tags
spawn: skip (parent implemented)

## Shipped

- RPC `assign_owner_products` (`ate/worker/server.py`) -> `ate/core/new_product.assign_owner_products`
- Match inventory / `parts/*.yaml`; unmatched listed (no scrape)
- `replace_owner_parts` / `unassign_owner_parts` in `database.py` (folders stay)
- Setup `#person-sku-input` / `#person-sku-chips` in setup-more; Save calls assign with `replace_parts`
- Chip x unassigns yaml only
- Checks: `check_assign_owner`, `check_operator_tree`, `check_ui_contract` exit 0
- Worker idle-restarted; Ctrl+F5 for UI (`?v=20260914a22`)

## Literal migrate

Upsert `parts:` + `ensure_product` Version_1 for **this** operator. Jane sibling does not clobber Ariff workbook/sessions.

## Next waves (do not start in A22 sitting -- handoff only)

1. **A23** typed `FORGET {label}` on Forget (same Setup person panel)
2. **A24** Version `_manifest/limits.yaml` + params overlay (PSU/AWG knobs)
3. **A25** same-family suggest-enable (no `btn-copy-tests`)
4. **A26** named test groups in `test_catalog.yaml`

## Parked

A13, A14, folder delete on Forget, Users table, scrape RUN-IC.
