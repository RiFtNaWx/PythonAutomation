---
keywords: prd-002, operator-profile, assign-skus, ensure-product, forget-passphrase, limits-overlay, suggest-import, named-groups, a22
main_idea: Founder profile ask is PRD-002 not a Users table. Assign = owners.yaml parts + ensure_product for this operator only. A22 READY; A23-A26 blocked. Do not move Ariff trees or unpark A14.
---

# 2026-09-14 Operator profile workflow (PRD slice)

PREFLIGHT: PARTIAL
reuse: docs/subagents_findings/2026-09-13_campaign-tests-page.md, 2026-09-11_scale-operator-tree.md, 2026-09-11_codeless-owner-tags.md, 2026-09-08_f23-detect-wrap-copy-version.md, 2026-09-13_vibe-code-add-test-tickets.md
spawn: skip

## Nearness

Artifact checked: Setup `btn-save-person` / `btn-forget-person` in `ate/ui/web/index.html` + `app.js`; `upsert_owner` / `remove_owner` in `ate/core/database.py`; `ensure_product` in `ate/core/new_product.py`; `load_part_specs` in `ate/core/specs.py` (no `_manifest` overlay); Tests version-gaps skip other operators. Live 5174 not clicked this turn.

Gap: Save person writes yaml and tells the operator to Apply the on-screen SKU. Forget is `confirm()` only. Limits are shared. Copy-from-part UI parked. Groups are fixture_mode only.

## Translate (literal -> shall)

| Founder words | Shall | Shall not |
|---------------|-------|-----------|
| Auto-assign related products + create folders | upsert `parts:` + `ensure_product` Version_1 for this operator on matched inventory/part-yaml SKUs | Move/copy Ariff/ChangThong/Eugene sessions or xlsx |
| Remove self from a product | drop `parts:` entry | Delete folders |
| Remove person + passphrase | confirm + type `FORGET {label}`; yaml-only default | Users/login; folder delete unless founder unparks |
| Tune limits/specs | `_manifest/limits.yaml` last-wins | Clobber shared `ate/config/limits/` |
| Import existing tests; suggest by type -> part | enable registry ids on this Version catalog | Merge another person's files; copy-from-part wholesale; no-code wizard |
| Drag/add/name groups | Tests-page `test_catalog.yaml` `groups:` list order | A14 xyflow canvas |

## Epic order

1. A22 assign + ensure folders (READY, inspectable)
2. A23 typed-phrase Forget (blocked: same Setup person panel)
3. A24 Version limits overlay
4. A25 same-family suggest-enable (`btn-copy-tests` stays absent)
5. A26 named groups (after A25)

WIP: A22 only. Tickets not filed (prd-agent does not cut tickets).

## Files written this turn

- `docs/prd/PRD-002-operator-profile-workflow.md`
- `docs/epics/EPIC-A22-operator-assign-folders.md` through `EPIC-A26-named-test-groups.md`
- PRD-001 F26 append; SHIP_NEXT; tickets INDEX; STATUS.md

## Founder defaults (3)

1. Folder delete on Forget = PARKED
2. Publish overlay to shared limits = PARKED
3. Other-operator folders stay skipped; enable registry ids onto this catalog is allowed; wholesale other-SKU enabled_tests copy stays refused

## Next

Epic-agent Mode A on EPIC-A22 only. Implement Composer 2.5. Validate Grok 4.5/4.6. No code in this sitting.
