# PRD-002 - Operator profile, assign SKUs, this-Version limits, same-family import, named groups

**Product:** PythonAutomation ATE (operator console + worker)
**Owner:** founder
**Status:** READY to slice. Mode A authoring complete. Do not implement in this document wave.
**Baseline:** [PRD-001](PRD-001-ate-multi-product-platform.md) (A01-A21 stay closed or leftover-honest). Do **not** reopen A01-A21 as new work.
**Repos in scope:** this repo (`PythonAutomation` / origin `jian-hong/Python_Automation_JH`)
**Created:** 2026-09-14
**Updated:** 2026-09-14 (F1 founder: add person starts SKU workflow; forget with passphrase; this-Version limits; suggest import; named test groups)
**Epic home:** A22 at `docs/epics/EPIC-A22-operator-assign-folders.md` (READY). A23-A26 blocked until prior closes. Do **not** open GitHub Issues. Ticket files stay under `docs/tickets/` after epic-agent Mode A.
**Parked (inherited):** A13 OneDrive Excel MCP, A14 xyflow, no-code wizard, ML trainer, delete `main.py`.

---

## 0. Nearness (this run)

**Artifact checked (files, not a live 5174 click this turn):** Setup person panel in `ate/ui/web/index.html` (`btn-save-person`, `btn-forget-person`, `person-hint`) and `ate/ui/web/app.js` `savePersonFromSetup` / forget `confirm()`. Tests page version-gaps in `ate/core/test_detect.py` (other operator folders `skipped`, `copy_between_people: false`). Limits load in `ate/core/specs.py` `load_part_specs` (shared `ate/config/limits/<key>.yaml` then part yaml; no `_manifest/` overlay).

The live product is the operator console (`ate/` + worker **8766** + UI **5174**). This slice is closer to "new person gets their SKU folders without stealing Ariff's tree" than to a Users/login product. A green invisible RPC without a Setup click path does not count as nearer.

**Analog / TAS:** There is no TAS-ATE lane. Live surface is this console. Frozen analog (LabAutomation-1 / vendor trees) is Path C ingest only. Verdict: **extend-live**. SKIP a second clone. BAN n8n / grok-bot / AGPL / leaked trees. Palantir P1 stays parked. Do not redesign left rail / fonts / UI_CONTRACT chrome.

---

## 1. Press release

### New person. Their product codes. Their folders. Nobody else's workbook.

**Subheading:** Lab leads add Jane, pick the SKUs she runs, and the console creates Jane's Version_1 trees beside Ariff and ChangThong -- then Jane can drop a SKU, forget her yaml row with a typed phrase, tune min/max on her Version, and enable tests that already exist in this family.

**Problem:** "Save person writes `owners.yaml` and tells me to Apply campaign for the one SKU on screen. Forget is a browser confirm with no typed phrase. Limits are shared for every operator of that part. Copy-from-part is parked because RS0204 dual-rail ids must not land on RS1G07. Groups are fixture modes, not named lists Jane can add. I asked for a profile workflow and the console still treats person as a folder name plus a picker list."

**Solution:** One profile workflow on Setup (not a Users table). Assigning product codes upserts `owners.yaml` `parts:` and `ensure_product` for **this** operator's Version_1 only. Forget person stays yaml-only unless the founder unparks folder delete, and both paths require typing `FORGET {label}`. Per-person min/max lives in that Version `_manifest/limits.yaml`. Suggest-import lists registry ids classified family -> part, plus this operator's other Versions; other people's folders stay skipped. Named groups are `test_catalog.yaml` labels on the Tests page, not an xyflow canvas.

**Quote:** "I typed Jane, picked RS1G08 and RS1G07, and Jane's folders appeared next to Ariff. Ariff's workbook did not move. Forget asked me to type FORGET Jane. I changed Jane's ICC max on her Version without rewriting the shared limits file." - characterization lead, internal (aspirational)

**Call to action:** Slice **EPIC-A22** only this wave. A13/A14 stay parked.

---

## 2. FAQ

### External

- **What is shipping in this slice?** A Setup profile workflow: pick product codes -> assign + create this person's folders; later unassign a SKU; forget person with a typed phrase; this-Version limits overlay; same-family suggest-enable of existing TestSpec ids; named test groups on the Tests page.
- **Will Ariff's RS1G08 tree change when Jane is added on the same SKU?** No. Jane gets a sibling operator folder. Sessions and xlsx stay where they are.
- **Is this login?** No. No password, no Users SQL table, no Tags/Users path axis. Passphrase means type-to-confirm.
- **Can Jane drag groups on a canvas?** No. A14 xyflow stays parked. Groups are named lists on the Tests page (enable / order / labels).
- **Does import copy Python from another person?** No. Import = enable existing registry ids on this Version catalog, and/or Path C wrap of golden `test_*` into this campaign family. Scaffolds are not done.

### Internal

- **What could make this fail?** Interpreting "migrate related products to him" as copy/move of Ariff/ChangThong/Eugene sessions or xlsx. Second: Forget deleting other operators' trees. Third: writing shared `ate/config/limits/` from a person editor and clobbering every operator of that SKU. Fourth: unparking `btn-copy-tests` and copying RS0204 enabled lists onto RS1G07. Fifth: a Users table or login because "passphrase" was in the ask.
- **What are we assuming?** (1) `owners.yaml` `parts:` stays a picker list, not an ACL. Anyone can still Apply a SKU they type. (2) `ensure_product` / `ensure_version` already create `#Test_Database/{Component}/{Part}/{Package}/{Operator}/{Version_N}/`. (3) Catalog `enabled_tests` already wins over part yaml. (4) `load_part_specs` can grow a last-wins overlay without reopening A20 rON-image leftover. (5) Version-gaps already skip other operators.
- **What would we have to be right about?** That "related products" means inventory/part-yaml SKUs that already exist (auto-assign those codes + ensure this person's folders), not a graph of "similar parts" and not a MOVE of another person's campaign.
- **Why not reopen A16 copy-from-part?** Copy-from-part was parked to stop cross-SKU enabled-list merge. A25 unparks **enable existing ids** on this Version (same family). Wholesale copy of another part's `enabled_tests` stays refused.
- **GitHub Issues?** Still no unless the founder opts in.

---

## 3. Out of scope

Explicit park / refuse for this PRD:

- Users SQL table, login, auth, password hashing, Kevin observer becoming a login
- Tags or Users folder axis under `#Test_Database`
- Moving or copying another operator's `workbook/` or `sessions/` into the new person
- Deleting other operators' trees
- Folder delete on Forget (default). If later unparked: passphrase + type-the-label, this operator's trees only -- still not this PRD's A22/A23 default
- A13 OneDrive Excel MCP / Graph / second Excel writer
- A14 xyflow / drag-drop canvas / Figma layout
- No-code wizard; in-browser Monaco; pasting vendor trees into `ate/`
- Copy Ariff Python or catalog files into Eugene; wrap into another family
- Cross-family copy (RS0204 dual-rail ids onto RS1G07 via enabled-list clone)
- Scraping en.run-ic.com into `#Test_Database`
- Rewriting left rail, fonts, tab chrome, UI_CONTRACT "to look modern"
- Reopening A01-A21 as new implement work (A19/A20 leftovers stay honesty gaps: VOX corners, RS2323 rON image)
- Shared `ate/config/limits/` or `parts/*.yaml` as the default save target of the person editor
- Delete `main.py` / dual-stack
- ML trainer

---

## 4. Success assertion

Testable from the operator seat (full PRD; **this wave is A22 only**):

> **WHEN** an operator types a new person (not All / Kevin) and selects product codes that already exist in inventory or part yaml, **THE SYSTEM SHALL** upsert that person in `owners.yaml` with those codes on `parts:` and **SHALL** `ensure_product` Version_1 for **that** operator on each matched SKU, and **SHALL NOT** copy or move another operator's `workbook/` or `sessions/`.
>
> **WHEN** that person unassigns a product code in profile setup, **THE SYSTEM SHALL** drop it from `owners.yaml` `parts:` and **SHALL NOT** delete Version folders.
>
> **WHEN** an operator forgets a person, **THE SYSTEM SHALL** require a typed phrase `FORGET {label}` (plus a confirm) before dropping the yaml row, and **SHALL NOT** delete folders in the default path, and **SHALL NOT** remove All or Kevin.
>
> **WHEN** that person edits min/max on their Version, **THE SYSTEM SHALL** persist `_manifest/limits.yaml` for that campaign and **SHALL** use it last-wins for STS/P-F on that Version, and **SHALL NOT** rewrite shared `ate/config/limits/` unless a later founder-unparked "every operator of this SKU" action is taken.
>
> **WHEN** test ids already exist in this family's registry, **THE SYSTEM SHALL** suggest them classified family -> part -> tests and **SHALL** enable selected ids on **this** operator Version catalog, and **SHALL NOT** merge another operator's catalog files or wrap into another family.
>
> **WHEN** the operator names a test group on the Tests page, **THE SYSTEM SHALL** store group labels and member ids in this Version `test_catalog.yaml`, reorder as list moves (not a canvas), and **SHALL NOT** change the left-rail family switcher.

---

## 5. Code-verified baseline (do not rebuild)

Checked 2026-09-14 against the working tree:

| Area | State | Evidence |
|------|-------|----------|
| Add person | Setup Operator + Save person / Apply -> `upsert_owner` | `ate/core/database.py` `upsert_owner`; UI `savePersonFromSetup`; hint still says Apply to create folders |
| `parts:` | Picker list, not ACL | `AGENTS.md`; `owners.yaml` |
| Folders | 5-level path; two people = two folders | `ensure_product` / `ensure_version`; `check_operator_tree`; finding `2026-09-11_scale-operator-tree.md` |
| Forget | yaml row only; `confirm()` only; folders stay | `remove_owner`; `btn-forget-person` |
| Tests Path A/B/C | catalog / TestSpec / wrap scaffold | `docs/VIBE_CODE.md`; `check_add_test` |
| Copy-from-part | PARKED | `check_ui_contract` fails if `btn-copy-tests` / `detect-copy-from` exist |
| Version gaps | this operator Versions + part yaml; other ops skipped | `test_detect.py` `skipped_operators`, `copy_between_people: false` |
| Limits | shared yaml + A20 Fetch (local PDF first) | `ate/core/specs.py`; `ate/config/limits/` |
| Groups | fixture_mode batches | `registry.group_by_fixture`; family rail OpAmp/Logic/switch/level |
| Enable API | same-family ids; default catalog not part yaml | `enable_tests_on_part(..., update_part_yaml=False)` |

False premises refused: there is no Users table to extend; there is no per-person limits overlay yet; "drag groups" is not an existing canvas.

---

## 6. Model / dispatch law (this wave)

| Role | Model |
|------|-------|
| prd-agent / epic-agent / verify | Grok 4.5 or Grok 4.6 |
| implement | Composer 2.5 |
| ticket-runner default | Composer 2.5 unless founder overrides |

**WIP:** at most two epics in flight; at least one human-inspectable. A22 is inspectable (Setup). **Do not pair A23 with A22** -- both own the Setup person panel (`app.js` / `index.html` / `database.py` owner helpers). A23 waits for A22 close.

**F-0009:** one writer per working tree. No GitHub Issues.

---

## 7. Epic sketches (irreversibility order)

Epics are sketches here. Epic-agent owns ticket files. Appetite: one focused agent wave unless noted. Do not reopen A01-A21.

Ordering law: irreversibility, not value. A22 before A23 before A24 before A25 before A26.

### EPIC-A22 - Assign product codes and create this person's folders

| Field | Value |
|-------|-------|
| Tier | foundation (owner `parts:` + ensure trees) + visible Setup surface |
| Repo | this repo |
| Contract impact | additive (`upsert_owner` parts list + batch `ensure_product`; optional assign RPC) |
| Depends on | none (A15 path already shipped) |
| Blocks | EPIC-A23, and A25 suggest that lists this person's SKUs |
| Appetite | 1 wave |
| Status | **READY** |
| File | `docs/epics/EPIC-A22-operator-assign-folders.md` |

**Buyer-visible outcome:** Type Jane, pick existing SKUs (example RS1G08 + RS1G07), Save. Jane appears in owners. Jane/Version_1 folders exist for those SKUs. Ariff's RS1G08 tree is untouched. Jane can later uncheck a SKU; yaml `parts:` drops it; folders stay.

**Acceptance:**
> WHEN the operator saves a new person with product codes that match inventory or part yaml, THE SYSTEM SHALL upsert `owners.yaml` `parts:` for that label and SHALL create `#Test_Database/{Component}/{Part}/{Package}/{Jane}/Version_1/` for each matched SKU via `ensure_product`, and SHALL NOT copy another operator's workbook or sessions. WHEN a code does not match inventory or part yaml, THE SYSTEM SHALL report it unmatched and SHALL NOT scrape en.run-ic.com. WHEN the person unassigns a matched code, THE SYSTEM SHALL remove it from `parts:` and SHALL NOT delete folders. WHEN operator is All or Kevin, THE SYSTEM SHALL refuse the write.

**Design constraints (for tickets, not pre-solved here):**
- Reuse `upsert_owner` + `ensure_product` + `_inventory_match` / `part_key_for`. Do not change `DbContext.root()` shape.
- "Related products" = the SKUs they typed/picked that already exist, plus that row's package/component from inventory. Not a similarity graph.
- `parts:` remains a picker default, not an ACL.
- Human-inspectable: founder can add a temp person on a temp or unused SKU list and see sibling folders.

**Out of epic:** passphrase Forget (A23); limits overlay (A24); suggest-import (A25); named groups (A26); folder delete; Users table.

---

### EPIC-A23 - Typed-phrase Forget and confirm

| Field | Value |
|-------|-------|
| Tier | boundary (destructive-adjacent gate) |
| Repo | this repo |
| Contract impact | additive (`remove_owner` requires `confirm_text`) |
| Depends on | EPIC-A22 (do not dual-write Setup person panel) |
| Blocks | none |
| Appetite | 1 wave |
| Status | **BLOCKED** on A22 |
| File | `docs/epics/EPIC-A23-forget-passphrase.md` |

**Buyer-visible outcome:** Forget person asks confirm AND the operator types `FORGET Jane`. Yaml row drops. Folders stay. All/Kevin cannot be forgotten.

**Acceptance:**
> WHEN the operator clicks Forget person without typing `FORGET {label}` (case-sensitive label as shown), THE SYSTEM SHALL refuse `remove_owner` and SHALL leave `owners.yaml` unchanged. WHEN the typed phrase matches, THE SYSTEM SHALL drop the yaml row only and SHALL NOT delete Version folders. WHEN the target is All or Kevin, THE SYSTEM SHALL refuse.

**Out of epic:** folder delete (parked); login; A22 assign.

---

### EPIC-A24 - This-Version limits overlay

| Field | Value |
|-------|-------|
| Tier | capability (per-Version specs) + visible editor |
| Repo | this repo |
| Contract impact | additive (`_manifest/limits.yaml` last-wins in `load_part_specs`) |
| Depends on | A20 shared limits already exist; does not reopen A20 leftovers |
| Blocks | none required for A25 |
| Appetite | 1 wave |
| Status | **BLOCKED** until A22 wave done (WIP). Can start after A22 if A23 still blocked, but not same sitting as A22 if `specs.py` + Tests page also move in A25. |
| File | `docs/epics/EPIC-A24-version-limits-overlay.md` |

**Buyer-visible outcome:** Jane sets ICC max on her RS1G08 Version. STS/P-F on Jane's runs use that overlay. Shared `ate/config/limits/rs1g08.yaml` and Ariff's tree stay.

**Acceptance:**
> WHEN this Version `_manifest/limits.yaml` defines a spec id, THE SYSTEM SHALL use that min/max last-wins for enrich/judge on that campaign. WHEN the overlay is absent, THE SYSTEM SHALL keep A20 shared yaml + part yaml behavior. WHEN the operator saves overlay values, THE SYSTEM SHALL NOT write `ate/config/limits/` or `parts/*.yaml` in the default path.

**Out of epic:** A20 rON image leftover; website scrape; "publish to every operator of this SKU" (parked until founder unparks).

---

### EPIC-A25 - Same-family suggest and enable existing tests

| Field | Value |
|-------|-------|
| Tier | capability (import-as-enable) + Tests page surface |
| Repo | this repo |
| Contract impact | additive suggest payload; `btn-copy-tests` stays absent |
| Depends on | A16 Path A/C; A22 SKU list helpful |
| Blocks | EPIC-A26 (both own Tests catalog UI -- do not fly together) |
| Appetite | 1 wave |
| Status | **BLOCKED** on A22 (WIP) and must not overlap A26 or A27 |
| File | `docs/epics/EPIC-A25-same-family-suggest-import.md` |

**Buyer-visible outcome:** On Jane's RS1G08 Tests page, suggestions are grouped Logic -> RS1G08 -> registry ids (cin, cpd, ...). Jane enables ids onto her Version catalog. Ariff's catalog files are not copied. Other operator folders stay in the skipped list. Cross-family enable still refuses.

**Acceptance:**
> WHEN the Tests page loads, THE SYSTEM SHALL list suggest-enable ids classified family -> this part -> tests (registry + this operator's other Versions + part yaml / sheet_map), and SHALL keep other operators listed as skipped not merged. WHEN Jane enables an id that exists in this family registry, THE SYSTEM SHALL write this Version `test_catalog.yaml` only. WHEN the id is not in this family registry, THE SYSTEM SHALL refuse. WHEN dest family != source family, THE SYSTEM SHALL refuse. Path C wrap SHALL remain a scaffold.

**A27 note (2026-09-15, F3):** the wrap-scaffold sentence is superseded for the wrap action by PRD-003. This epic stays suggest-enable only. Do not fly with A27.

**Out of epic:** `btn-copy-tests` wholesale copy-from-part; no-code wizard; wrap into another family; A14; A26 groups.

---

### EPIC-A26 - Named test groups on the Tests page

| Field | Value |
|-------|-------|
| Tier | surface (catalog group labels / order) |
| Repo | this repo |
| Contract impact | additive `test_catalog.yaml` `groups:` |
| Depends on | EPIC-A25 (same Tests page + catalog schema) |
| Blocks | none |
| Appetite | 1 wave |
| Status | **BLOCKED** on A25 |
| File | `docs/epics/EPIC-A26-named-test-groups.md` |

**Buyer-visible outcome:** Jane names a group (example "DC leakage"), adds ids, reorders with up/down (not drag canvas). Run checkboxes still follow `enabled_tests`. OpAmp fixture groups can seed labels (BUFFER / G11) without rewriting the left rail.

**Acceptance:**
> WHEN the operator adds or renames a group and saves this Version, THE SYSTEM SHALL persist group label + member ids in `_manifest/test_catalog.yaml`. WHEN they reorder groups or members, THE SYSTEM SHALL persist order as lists. WHEN A14 xyflow is still parked, THE SYSTEM SHALL NOT add a canvas. WHEN `enabled_tests` hides an id, THE SYSTEM SHALL NOT run it just because it sits in a group.

**Out of epic:** A14; left-rail rewrite; new family packages.

---

## 8. File contention (named so writers do not collide)

| File | Owner epic | Do not also edit in |
|------|------------|---------------------|
| `ate/core/database.py` `upsert_owner` / parts assign | A22 | A23 except `remove_owner` after A22 |
| `ate/ui/web/app.js` + `index.html` Setup person panel | A22 then A23 | not both in flight |
| `ate/core/new_product.py` `ensure_product` | A22 (call, do not reshape path) | A23-A26 |
| `ate/core/specs.py` overlay | A24 | do not reopen A20 leftover tickets |
| `ate/core/test_detect.py` + Tests page catalog | A25 then A26 | not both in flight; **not with A27** |
| `ate/core/database.py` `DbContext.root()` path shape | **nobody** | all of A22-A26 |

---

## 9. Feedback ledger

Append only. Never rewrite prior rows.

| # | Date | Raised in | Feedback | Routed to | Outcome |
|---|------|-----------|----------|-----------|---------|
| F1 | 2026-09-14 | founder session (PRD-002) | Add user starts workflow: say product codes; if SKUs exist, auto-assign related products and auto-create folders. Later remove self from a product. Person can be removed with confirm AND typed code/passphrase. Select product codes; tune parameters/limits/specs; everyone can define min/max; check and improve. If test codes exist, learn what people used, import into this section, suggest import classified product type -> part number -> tests. Group tests like opamp groups; drag groups; add groups; name groups. | **This PRD.** Translate: assign = `parts:` + `ensure_product` this operator only (not move trees). Unassign SKU = drop `parts:` entry. Forget = typed `FORGET {label}` + yaml-only. Limits = Version overlay not shared yaml. Import = enable existing registry ids on this Version; other ops skipped. Groups = catalog labels not xyflow. | **Ack.** WIP: **A22 only**. Epic-agent next: Mode A on EPIC-A22. No tickets by prd-agent. No code. A01-A21 not reopened. A13/A14 parked. |
| F2 | 2026-09-15 | founder session | Specify who handles which documents; filter products this operator owns (folder-open already tracked); search tests; wrap family default same category but import from other products and filter by product. | Setup `#part-scope` Mine + first-run `#first-run-filter-who` (owners.yaml parts + disk folders + pic). Search on Test program / Path A / wrap. Wrap `#detect-product` same-family SKU filter; `#detect-family` stays locked. Progress board Part + Opened. Not Users table, not wrap-into-another-family, not `btn-copy-tests`. A25 full suggest-enable still later. | **Shipped UI 2026-09-15.** Ctrl+F5 `?v=20260915mine1`. |
| F3 | 2026-09-15 | founder session (PRD-003) | Remember snippet location; UI scans/triggers; original code stays SoT. Opposite of no-code wizard. | **Does not map to an open A22-A26 implement ticket.** Founder authorized **PRD-003 / A27**. A25 "Path C wrap remains a scaffold" is superseded for the wrap action only; suggest-enable stays A25. Do not fly A25/A26 with A27 (`test_detect.py` + Tests page). Do not reopen A16. | **Ack.** Routed out of this PRD. No A22-A26 scope widen. |

---

## 10. Founder decisions (do not invent a fourth)

Defaults used in this slice. Change only by appending the ledger.

1. **Folder delete on Forget:** PARKED. Default remains yaml-only even after the typed phrase. Unpark later needs passphrase + type-the-label and still must not delete other operators' trees.
2. **Publish overlay to shared `ate/config/limits/`:** PARKED. A24 overlay is this Version only.
3. **Other-operator same-SKU suggest:** SHOW as skipped (already). Enabling an id that exists in **this family registry** onto **this** catalog is allowed in A25; copying the other person's files/xlsx/Python is refused. Wholesale copy of another SKU's `enabled_tests` stays refused (RS0204 trap).

If the founder wants folder delete in A23 or shared-limits publish in A24, append a ledger row before epic-agent cuts those tickets.

---

## 11. Recommended next action

1. Epic-agent **Mode A** on **EPIC-A23** when that profile wave is seated (local ticket files; no GitHub Issues).
2. Pointer+trigger is **PRD-003 / A27**, not this PRD. Do not fly A25/A26 with A27.
3. Do not start A24-A26 in the same sitting as A27. Keep A13/A14 parked.

**Ports:** 8766 / 5174. Idle-restart worker after owner/RPC changes. Ctrl+F5 if UI only.
