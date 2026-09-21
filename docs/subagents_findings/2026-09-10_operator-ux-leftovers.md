---
keywords: operator-ux, owner-select, db-operator, applyDb, unassigned, tags-duplication, combo-change, all-view-only, lim-seelim, version-reset, post-combo-tags
main_idea: Combo/tags work fixed dropdowns and map-coverage false-OK, but two Operator pickers still desync, every campaign combo change runs full applyDb, _unassigned stays selectable, and Setup shows tags three ways while header All does not block writes.
---

# 2026-09-10 Operator UX leftovers (post combo/tags)

PREFLIGHT: PARTIAL. Reuse: 2026-09-08_operator-flow-e2e-review, 2026-09-09_operator-default-eugene, 2026-09-10_combo-tags-excel. Spawn: skip.

## Closed since 2026-09-08 (do not re-open)

- Default campaign landing on empty `_unassigned` when Eugene tree exists (`prefer_live_operator`, `bench.yaml` Eugene path, `pickLiveOperator`)
- Map coverage string `OK: 0` (`loadMappedCoverage` now says `Map coverage empty` when `n_map === 0`)
- Advanced bench panel hidden when manual mode on but no tests ticked (`applyTestDefaults` toggles `#param-advanced` before early return)
- DEMO Run timeline 0/0 (`paintDemoTimeline` on demo RPC result)
- Native datalist dead on Windows (`fillCombo` + `#ate-combo-menu`)

## Ranked open bugs (UI/js/css fixes only)

### 1. Two Operator pickers disagree (header vs Setup folder)

**Where:** `app.js:207-233` (`applyOwner`), `app.js:235-247` (`writeOperatorLabel` / `requireWriteOperator`), `app.js:2098-2129` (`db-operator` change handler)

**Operator sees:** Header says Eugene; Setup Operator folder says Ariff (or the reverse). Breadcrumb and lab xlsx follow the folder field. Writes use `db-operator` first (`requireWriteOperator`), so START/DEMO/New product hit the folder name, not the header label.

**Also:** Family rail restores per-family saved operator (`readSavedByFamily` at `2067-2084`) without updating `#owner-select`.

**Smallest fix:** On `db-operator` change (and after `applyDb`), set `#owner-select` to the matching `ownersList` row by label, or show a visible mismatch hint on `#db-breadcrumb` when they differ. Mirror sync when header changes (already via `applyOwner`).

---

### 2. Header Operator=All does not block writes

**Where:** `app.js:178-183` (`readSavedOwner` defaults `"all"`), `app.js:217-219` (`applyOwner` no-op for `all`), `app.js:242-247` (`requireWriteOperator` ignores header when `db-operator` has a person name)

**Operator sees:** Hint says "All is view-only", but Create folders / DEMO / START still work because `#db-operator` is auto-filled to Eugene (or first live folder) via `pickLiveOperator` (`1563-1567`).

**Smallest fix:** In `requireWriteOperator`, reject when `#owner-select` value is `all` regardless of `#db-operator`. Optionally default `readSavedOwner()` to `eugene` instead of `all`.

---

### 3. Every campaign combo change runs full `applyDb`

**Where:** `app.js:2098-2129` (change listeners on `db-component` through `db-version`), `app.js:1840-1888` (`applyDb` RPC chain)

**Operator sees:** Picking Part, Package, Operator, or Version immediately logs "Campaign applied", reloads tests, tags, detected scan, and map coverage -- without clicking Apply campaign. Typing a new `Version_N` and changing another field can call `ensure_version` (`1844-1862`) before the operator intended.

**Smallest fix:** On combo `change`, call `refreshDbCascades()` + update breadcrumb only; keep `applyDb()` for `#btn-apply-db`, family rail commit, `applyOwner`, and explicit create flows. Or debounce + confirm when version string is new.

---

### 4. `_unassigned` still appears in Operator folder list

**Where:** `app.js:1558-1567` (`refreshDbCascades` -- lists all tree operators), `database.py:571-577` (`list_tree` keeps legacy `_unassigned`)

**Operator sees:** Operator folder dropdown can include `_unassigned`. Default selection skips it (`pickLiveOperator` at `143-148`), but manual pick opens an empty legacy tree with no person workbook.

**Smallest fix:** Filter `_unassigned` out of `operators` before `fillCombo($("db-operator"), ...)` (same filter as `pickLiveOperator` live list).

---

### 5. Header operator switch always jumps to Version_1

**Where:** `app.js:217-230` (`applyOwner` hardcodes `version: "Version_1"`)

**Operator sees:** Picking a person in the header resets Version to `Version_1` even when that person already has `Version_2` on disk.

**Smallest fix:** After `paintCampaign`, set version to latest existing for that operator/part (`versionsForSel` max) when present; only default `Version_1` when none exist.

---

### 6. Lim header vs SeeLim live workbook (inventory pic)

**Where:** `owners.yaml:33-46` (Lim default_part RS2323), `inventory.yaml` RS2323 `pic: seelim`, `app.js:217-230` (`applyOwner` uses owners.yaml only)

**Operator sees:** Header Operator Lim opens `.../Lim/Version_1` (often empty). Live RS2323 report is under SeeLim per tracking sheet.

**Smallest fix:** In `applyOwner`, when `default_part` has an inventory row, prefer `operatorFromPic(row.pic)` over owners label for the folder field (one line in `applyOwner` / `campaignFromInventory` reuse).

---

### 7. Setup tags shown twice (Tags row + Add labels chips)

**Where:** `index.html:109-141`, `app.js:1353-1365` (`addCampaignTagFromText` -> `addSetupLabel`), `app.js:1798-1804` (`paintTagsEditor`)

**Operator sees:** Adding a board via Tags input or Add labels puts `board:REV` on `#db-tag-chips` and the same token on `#setup-label-chips`. Tags page `#tags-editor-chips` is a third view of the same `campaignTags`.

**Smallest fix:** Drop `#setup-label-chips` (keep Kind/Value add only) or hide `#db-tag-input` on Setup and point to Tags tab. Minimal: one chip row on Setup + hint "full editor on Tags tab".

---

### 8. Tags import omits structured labels

**Where:** `app.js:2243-2258` (`btn-tags-import` sets `campaignTags` / `campaignBoards` only)

**Operator sees:** Import from another campaign root shows tags on chip row but drops `campaignLabels` / board-type entries that Setup Add labels expects.

**Smallest fix:** After import RPC, assign `campaignLabels = res.labels || []` and call `paintTagsEditor()`.

---

### 9. Photo path hint can say ORT on non-OpAmp campaigns

**Where:** `database.py:182-199` (`_default_photo_test_key` ORT fallback), `app.js:1581` (`db-path-hint`)

**Operator sees:** `#db-path-hint` ends in `.../ORT/DUT_1/screenshots` on Logic/Level campaigns with no ORT folder yet.

**Smallest fix:** UI suffix when path contains `/ORT/` and active family is not opamp: "(OpAmp default -- apply campaign with sheet_map)". Or pass family into `photo_preview` and skip ORT fallback for logic/switch/level.

---

### 10. Board combo on Tags page auto-adds on pick

**Where:** `app.js:1205-1210` (`applyComboPick` for `tag-board-select`)

**Operator sees:** Clicking a board in the dropdown immediately adds and saves; Add board button is redundant and easy to double-add by accident.

**Smallest fix:** For `tag-board-select`, set input value only on pick; require `#btn-tag-add-board` click to commit (match Setup Add label pattern).

---

## Not ranked (parked or hardware)

- A13 paste / A14 xyflow Excel unpark
- START / Continue / VISA / instrument Discover (hardware path)
- Golden workbook screenshot embed (`check_golden_workbook` campaign data)

## Verify after fixes

```
python -m ate.core.check_ui_contract
python -m ate.core.check_operator_tree
```

Manual: Ctrl+F5 console; toggle header Operator vs Setup Operator folder; change Part without Apply and confirm tests/tags do not reload until Apply.
