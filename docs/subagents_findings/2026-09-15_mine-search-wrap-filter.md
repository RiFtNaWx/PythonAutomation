---
keywords: mine, part-scope, first-run-filter-who, search-tests, detect-product, wrap-family, pic, progress-board, ingestDbTree, check_ui_contract
main_idea: Mine filters Setup/first-run to this person's owners.yaml parts + disk folders + tracking PIC. Test search on Setup/Path A/wrap. Wrap stays this category; product filter imports other SKU goldens. Progress Who/Part/Opened. Every list_db_tree goes through ingestDbTree. Not a Users table.
---

PREFLIGHT: PARTIAL
reuse: 2026-09-14_a22-assign-skus-shipped.md, 2026-09-14_lala-local-operator-pref.md, 2026-09-14_operator-profile-workflow.md, 2026-09-13_campaign-tests-page.md
spawn: skip (parent implemented)

## Shipped

- Setup `#part-scope` Mine (default) / All tracking. Mine = `owners.yaml` `parts:` + `#Test_Database` operator folders (snapshot via `ingestDbTree` before inventory merge) + inventory `pic:`.
- First-run `#first-run-filter-who` Mine / All people / named PIC. Rows show PIC. Unknown name with empty Mine falls back to all tracking ticks.
- Search: `#test-list-search`, `#campaign-test-search`, `#detect-search`.
- Wrap `#detect-product` (same category). `#detect-family` stays disabled in HTML + `fillDetectFamilySelect`.
- Progress board `#progress-board`: Who / Part / Opened (heartbeat `campaign`) / Last run / Runs / P/F / Idle / Seen.
- Plus package/operator refreshes via `ingestDbTree`, not raw `dbTree = await rpc("list_db_tree")`.
- Checks: `check_ui_contract` (board columns scoped to `#progress-board`, all `list_db_tree` wrapped, cache-bust match, Mine cascade). `check_progress` heartbeat campaign round-trip. Worker restart not required (static UI). Ctrl+F5 `?v=20260915mine4`.

## Trap

A string check for `<th>Part</th>` anywhere in `index.html` false-passes on `#progress-owned`. Scope to `#progress-board`. A string check for `dbTree = await rpc("list_db_tree")` misses spacing variants -- walk every `rpc("list_db_tree")` and require `ingestDbTree` in the 24 chars before it.

## Not

Users table. Wrap into another family. `btn-copy-tests`. A25 classified suggest-enable list (later).
