# A15-T01 - Operator folder + migrate + list_tree/UI

**Epic:** EPIC-A15
**PRD:** PRD-001 F22
**Status:** implemented (superseded by A15-T01-operator-folder.md; 5-level path + migrate live)
**Step:** current: 0 / 4
**Depends on:** none (first seam)
**Model (implement):** composer-2.5
**Model (verify/close):** Grok 4.5 high
**Adversary rule:** R-0003 -- implementer is never the verifier
**GitHub Issues:** do not open

---

## Problem

Campaign identity is 4-level: `#Test_Database/{Component}/{Part}/{Package}/{Version_N}`. `owners.yaml` is a person picker that jumps a default campaign. Session JSON has no operator folder field. Two people running the same part/package write into the same Version tree.

Evidence:

- `ate/core/database.py` `DbContext.root()` = component / part / package / version
- `list_tree` scans package -> `Version_*`
- `ate/core/new_product.py` `campaign_root` same 4-level
- `begin_session` writes `sessions/*.json` from `ctx.identity()` -- no operator
- `default_context` parses bench path as 4 segments after `#Test_Database`

---

## Acceptance

WHEN `DbContext.root()` / `campaign_root` / `ensure_product` / `set_context` run, THE SYSTEM SHALL use

`#Test_Database/{Component}/{Part}/{Package}/{Operator}/{Version_N}/`

with Operator = `owners.yaml` `id` (not `all`).

WHEN `list_tree` scans, THE SYSTEM SHALL list operators under package, then `Version_*` under each operator (including leftover 4-level trees only as migrate sources).

WHEN existing `{Package}/Version_*` trees exist, THE SYSTEM SHALL move them to `{Package}/ate/{Version_*}` (or the known owner id if the part maps to exactly one owner other than `all`/`ate`) without duplicating `_manifest` / workbook / sessions.

WHEN `begin_session` writes session JSON, THE SYSTEM SHALL include `operator` (id) and `operator_label`.

WHEN Setup campaign dropdowns render, THE SYSTEM SHALL insert Operator between Package and Version, driven by `list_tree` + `list_owners`. Picker `all` SHALL NOT create folders; New product / Apply SHALL require a real operator.

WHEN `python -m ate.core.check_new_product` runs, THE SYSTEM SHALL fail if `campaign_root` still omits operator or if a temp 4-level tree is not migrated.

WHEN no instrument session is open, THE SYSTEM SHALL keep START disabled (do not regress).

---

## Why it is not a one-liner

Trap: only painting an Operator dropdown while `root()` stays 4-level. Trap: copying trees instead of moving. Trap: using `all` as a folder. Trap: breaking bench.yaml path parse (4 vs 5 segments) so default campaign points at a missing Version.

---

## Files likely touched

- `ate/core/database.py` -- `DbContext.operator`, `root()`, `identity()`, `default_context` parse, `set_context`, `list_tree`, migrate helper, `how_to_use` axes
- `ate/core/new_product.py` -- `campaign_root(..., operator=)`
- `ate/worker/server.py` -- `set_db_context` / `ensure_product` pass operator
- `ate/ui/web/index.html` / `app.js` -- operator select in campaign row; `firstCampaignInComponent`; `applyOwner` writes that operator's folder
- `ate/core/check_new_product.py` -- 5-level + migrate assert
- `ate/config/bench.yaml` only if default path must gain `/ate/` after migrate (prefer code parse that accepts both during migrate)

Do **not** change PSU bring-up (T03). Do **not** invent Comparator tests (T02). Do **not** reopen A01-A12.

---

## Step

```
Step: current: 0 / 4
```

1. Path + identity + set_context/list_tree
2. Migrate existing 4-level trees
3. UI dropdowns + RPC; START gate unchanged
4. `check_new_product` fails without operator folder; idle worker restart

---

## Out

A13/A14; cloud; category suite honesty (T02); PSU hard-fail (T03); GitHub Issues
