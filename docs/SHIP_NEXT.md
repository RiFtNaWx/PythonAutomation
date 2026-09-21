# ATE ship plan -- next and upcoming

**Print this.** Companion to [STATUS.md](../STATUS.md) (what is live), [AGENTS.md](../AGENTS.md) (where to edit), [VIBE_CODE.md](VIBE_CODE.md) (how to add a test), [tickets/INDEX.md](tickets/INDEX.md) (every ticket).  
**Date:** 2026-09-15  
**Product:** operator console (`ate/` + worker **8766** + UI **5174**)  
**Rule:** one wave at a time. Do not unpark A13. A14 Recipe canvas unparked (PRD-005). Do not scrape en.run-ic.com into `#Test_Database`.

---

## 1. Wave order (do not skip)

| Order | ID | Name | Appetite | Depends on | Buyer sees when done |
|------:|----|------|----------|------------|----------------------|
| 0 | A18 | Living JSON merge + records | done | A17 | Subset START keeps old tests + timestamps |
| 1 | A19 | Standard Excel + numeric auto-fill | implemented; leftover VOX corners | A18 | Lab xlsx DUT cells fill from `report.json` |
| 2 | A20 | Limits everywhere + sheet-quality P/F PDF | implemented; leftover rON image | A19 + local PDFs | PASS/FAIL = datasheet min/max |
| 3 | A21 | Setup UX leftovers | done | none hard | Apply is intentional; Lim follows SeeLim |
| 4 | V07 | R-0003 verify A07-A12 | done 2026-09-13 | none | Independent pass notes; leftovers stay leftovers |
| 5 | A22 | Assign SKUs + this person's folders | implemented 2026-09-14 | A15 path | Jane picks codes; her Version_1 trees exist; Ariff untouched |
| 6 | A27 | Snippet pointer + trigger | 1 wave; **READY** (PRD-003) | A16 leftover | Detect remembers file:line; Wrap of clean fixture does not write imported_*.py; START runs original fn |
| 7 | A23 | Typed-phrase Forget | 1 wave; next on profile board | A22 | Forget requires `FORGET Jane`; yaml-only |
| 8 | A24 | This-Version limits overlay | 1 wave | A20 shared yaml | Jane min/max on her Version only |
| 9 | A25 | Same-family suggest-enable | 1 wave; not with A26 or A27 | A16 + A22 + A27 wrap contract | Tests page suggests registry ids; no copy-from-part |
| 10 | A26 | Named test groups | 1 wave | A25 | Tests-page groups in `test_catalog.yaml` |
| 11 | later | Stub suites / remaining thin OpAmp recipes | multi | founder asks | Comparator/... stay parked. Noise is 0.1-10 Hz Vpp (not nV/rtHz) |

**Parked forever until founder unparks:** A13 OneDrive Excel MCP, Monaco full editor, ML trainer, delete `main.py`. Folder-delete on Forget. Shared-limits publish from overlay. Unrestricted Python wizard stays banned (A14 is closed-opcode only).

**PRD:** [PRD-002](prd/PRD-002-operator-profile-workflow.md) for A22-A26. [PRD-003](prd/PRD-003-snippet-pointer-trigger.md) for A27. [PRD-005](prd/PRD-005-recipe-canvas.md) for A14. Do not reopen A01-A21 as new work. Do not reopen A16 tickets.

---

## 2. Already shipped (baseline for next)

Do not re-build these:

- Family rail + TestSpec packages + operator folder path
- Tags, Run ledger, photo paste via `sheet_map` `paste.photos`
- `sessions/report.json` **merge** (A18) + `{test_key}/DUT_n/records/`
- STS `sessions/datalog.md|.html|.pdf` (simple text PDF)
- Limits yaml per inventory part (`ate/config/limits/`). RS622 + RS0204 hand-kept. RS22X/RS32X family PDFs are opamps, not analog-switch/LDO.

Proof today:

```
python -m ate.core.check_tags_datalog
python -m ate.core.check_ui_contract
python -m ate.core.check_family_load
python -m ate.core.check_campaign_outline
```

---

## 3. EPIC-A19 -- Standard Excel + numeric auto-fill

### Goal

One fill path for every family: living JSON -> workbook cells. Photos already paste; **numbers** do not.

### Buyer outcome

Operator runs GBW then ORT on different days. Opens the campaign xlsx: both tests show latest values, DUT columns, PASS/FAIL where limits exist. Logic/LIM workbooks are not wrecked by OpAmp-only golden apply.

### Design (ponytail)

1. Extend campaign `_manifest/sheet_map.yaml` with optional `paste.values` (or `paste.results`) per test:

```yaml
tests:
  gbw:
    excel_sheet: GBW
    folder: GBW
    paste:
      photos:
        u1_chA: A91
      values:
        GBW_MHz: B12          # measurement id -> cell
        result: B13           # optional PASS/FAIL cell
```

2. New writer `ate/reporting/session_values.py` (mirror `session_paste.py`):
   - Read `load_report()` living JSON
   - For each step measurement with a mapped cell, write value (+ unit/result if mapped)
   - Skip `FILL_ME`
   - Locked xlsx -> write `{stem}_filled.xlsx` and set status (same pattern as tags)

3. Call from `end_session` after photo paste (and optional RPC `fill_workbook_from_report`).

4. Golden layout: keep OpAmp `TEST_SHEETS` as OpAmp-only. Add `apply_family_layout(family)` later if needed -- **A19 does not force Logic through ORT golden.**

5. Do **not** invent a second Excel stack. Do **not** unpark A13.

### Files to touch

| File | Change |
|------|--------|
| `ate/reporting/session_values.py` | new -- fill numbers from report.json |
| `ate/core/database.py` `end_session` | call fill after paste |
| `ate/worker/server.py` | optional RPC only if UI needs a button |
| `ate/core/check_session_values.py` | new self-check (temp xlsx + fake report) |
| one sample `sheet_map` | RS622 Version_1 values anchors for GBW or ORT |
| `AGENTS.md` | one row: numeric cells = sheet_map paste.values |
| `docs/epics/EPIC-A19-excel-autofill.md` | this epic |

### Tickets (cut when implementing)

| ID | Seam |
|----|------|
| A19-T01 | `session_values` + check (no UI) |
| A19-T02 | `end_session` hook + AGENTS + one RS622 sheet_map values block |

### Acceptance

> WHEN `report.json` has a measurement id mapped in `paste.values`, THE SYSTEM SHALL write that number into the campaign workbook cell on session end (or fill RPC). WHEN the cell is FILL_ME, THE SYSTEM SHALL skip. WHEN the workbook is locked, THE SYSTEM SHALL not crash the session; it SHALL report locked / alternate file. WHEN Logic campaign has no OpAmp sheets, THE SYSTEM SHALL NOT run OpAmp golden apply as a side effect of fill.

### Ship steps (agent)

1. Plan mode agree (Grok) -- confirm `paste.values` shape.
2. Implement Composer 2.5 -- T01 then T02.
3. `python -m ate.core.check_session_values`
4. Idle-restart worker (`restart_ate_worker.bat`).
5. Manual: Apply RS622 Eugene Version_1, DEMO or START one test with measurements, open xlsx, confirm cell.
6. Validate Grok 4.5 high.
7. Update `STATUS.md` (move A19 to Done).

### Time

About 2 to 3 hours if sheet_map anchors exist for one OpAmp test. Half day if first anchors must be measured on a live xlsx.

### Out of A19

A20 PDF polish; limits yaml for all parts; A13; rewriting golden_layout for Logic.

---

## 4. EPIC-A20 -- Limits everywhere + sheet-quality P/F PDF

### Goal

PASS/FAIL means datasheet min/max, not "script did not raise". Printable STS matches production Parameter / Unit / Min / Max / Typ / Value / Result.

### Buyer outcome

After a Version campaign, `sessions/datalog.pdf` (and md/html) lists every latest measurement with limits. Missing limits show `unspec`, not fake PASS. Logic RS1G08 / RS29511 / RS2323 have limits yaml like RS622.

### Design (ponytail)

1. **Limits first:** add `ate/config/limits/<key>.yaml` for parts we actually run (copy RS622 shape from `PROMPT_GUIDE.md`). English source: en.run-ic.com or attached PDF. Never scrape catalog SKUs.

2. **Stamp at record time** (already started in `database.record_step` + `specs.enrich_measurement`): every measurement gets min/max/typ/result. Extend so DEMO and live bodies return `{id, value, unit}` consistently.

3. **Coverage gate (optional UI later):** `report.json` `coverage` already has latest|missing. A20 can add `limits: stamped|missing` per test.

4. **PDF:** keep `ate/reporting/sts_datalog.py`. Improve layout (table columns, fail rows highlighted in HTML; PDF stays simple text or slightly better). Generate **after all enabled tests have a latest row OR operator clicks Export** -- not mid-START. Living merge already allows mixed old+new.

5. Root `limits.py` stays legacy. Console must not depend on it.

### Files to touch

| File | Change |
|------|--------|
| `ate/config/limits/rs1g08.yaml` (etc.) | new -- real min/max from datasheet |
| `ate/tests/**` run() returns | ensure measurements ids match limits |
| `ate/reporting/sts_datalog.py` | clearer columns; regenerate from merged report |
| `ate/core/check_specs_datalog.py` | new -- fail if enabled test has value but no result stamp when limits exist |
| `docs/epics/EPIC-A20-limits-pdf.md` | this epic |

### Tickets

| ID | Seam |
|----|------|
| A20-T01 | limits yaml for active inventory parts (rs622 done; rs1g08, rs29511, rs2323, rs0204) |
| A20-T02 | measurement stamp honesty + check |
| A20-T03 | STS export polish + "export when coverage complete" note in Results |

### Acceptance

> WHEN a measurement id exists in `ate/config/limits/<part>.yaml`, THE SYSTEM SHALL stamp `result` pass|fail|unspec on that measurement in `report.json`. WHEN value is outside min/max, THE SYSTEM SHALL mark fail (and step success false if any_fail). WHEN `export_sts` runs on living report, THE SYSTEM SHALL write md/html/pdf with Parameter Unit Min Max Typ Value Result. WHEN no limit exists, THE SYSTEM SHALL show unspec and SHALL NOT claim datasheet PASS.

### Ship steps

1. Author limits yaml (human + datasheet) -- agents fill empty min/max only.
2. Implement stamp check + STS polish.
3. Proof: `python -m ate.core.check_specs_datalog` + open `sessions/datalog.html` print-to-PDF.
4. Update STATUS.

### Time

Limits authoring: 1 to 2 hours per part with a datasheet. Code polish: about 2 hours.

### Out of A20

Excel number fill (A19). Full Noise/PSRR physics. Comparator suite.

---

## 5. EPIC-A21 -- Setup UX leftovers (printable punch list)

Source: `docs/subagents_findings/2026-09-10_operator-ux-leftovers.md` (some items already fixed -- re-check before coding).

| # | Bug | Ship fix | Done? |
|---|-----|----------|-------|
| 1 | Header vs Setup operator disagree | Sync `#owner-select` on `db-operator` change | done |
| 2 | All does not block writes | `requireWriteOperator` rejects header `all` | done |
| 3 | Combo change auto `applyDb` | Cascades + breadcrumb only; Apply button for RPC | done |
| 4 | `_unassigned` in list | Filter from combo | done |
| 5 | Header jumps to Version_1 | Prefer latest Version_N on disk | done |
| 6 | Lim vs SeeLim folder | Prefer inventory `pic` folder; keep existing disk package | done |
| 7 | Tags shown 2 to 3 times | Setup chip row hidden; Tags tab is the editor | done |
| 8 to 10 | Import labels / photo hint / board auto-add | Import sets labels; ORT hint on non-OpAmp; board pick does not auto-add | done |

**Ship:** one Composer pass on `ate/ui/web/app.js` + `check_ui_contract` + Ctrl+F5. No worker restart unless RPC added.

**Time:** about 1 to 2 hours.

---

## 6. V07 -- R-0003 verify A07-A12 (done 2026-09-13)

Independent. Finding: `docs/subagents_findings/2026-09-13_a07-a12-r0003-verify.md`. Did **not** reopen tickets to invent rON tables or Excel cells.

---

## 7. Later (not next)

| Item | Unlock |
|------|--------|
| Full Level / LDO / Power suites | Founder asks + recipes on disk |
| OpAmp Noise / PSRR / CMRR / AOL / EMIRR / PowerOn full bodies | After A19/A20; LA-1 recipe exists |
| Comparator / Interface / Vref / Clock / Data conversion | `run_ic.yaml` live:true only when suite exists |
| A13 Excel MCP / A14 xyflow | Explicit unpark |
| Delete legacy `main.py` | After console covers all daily goldens |

---

## 8. How agents ship (copy this)

```
Wave: A19 only.
Read STATUS.md, AGENTS.md, docs/SHIP_NEXT.md section 3.
Implement A19-T01 then A19-T02. Do not touch A20/A13/A14.
Run python -m ate.core.check_session_values.
Idle-restart worker. Update STATUS.md Done list.
Finding: docs/subagents_findings/YYYY-MM-DD_a19-excel-autofill.md
```

```
Wave: A20 only.
Read SHIP_NEXT.md section 4 and docs/PROMPT_GUIDE.md limits block.
Add limits yaml for parts we test. Do not scrape RUN-IC catalog.
Run check_specs_datalog. Update STATUS.md.
```

```
Wave: A21 UX only.
Read 2026-09-10_operator-ux-leftovers.md. Fix still-open rows only.
check_ui_contract. Ctrl+F5. No A19/A20 scope creep.
```

```
Wave: A22 only.
Read docs/prd/PRD-002-operator-profile-workflow.md and docs/epics/EPIC-A22-operator-assign-folders.md.
Epic-agent Mode A first (tickets). Then Composer 2.5.
Assign = owners.yaml parts + ensure_product this operator. Do not move Ariff trees.
Do not start A23-A26. A13/A14 parked.
check_operator_tree + check_new_product + check_ui_contract.
```

**Model handoff:** Plan Grok 4.5/4.6 -> Implement Composer 2.5 -> Validate Grok 4.5/4.6.

---

## 9. One-page calendar (printable)

| Week | Ship | Proof |
|------|------|-------|
| Now | A22 assign SKUs + folders (PRD-002) | Jane Version_1 beside Ariff; no xlsx copy |
| After A22 | A23 typed-phrase Forget | `remove_owner` refuses without `FORGET {label}` |
| After A23 | A24 Version limits overlay | overlay wins; shared yaml unchanged |
| Then | A25 then A26 | suggest-enable; named groups; no xyflow |
| Honesty leftovers | A19 VOX corners; A20 rON image | do not fake-close |
| Separate | V07 R-0003 A07-A12 | done 2026-09-13; leftover-honest A08/A10/A11 |

---

## 10. Stakeholder one-liner

**Done:** multi-product console, people folders, tags, living JSON merge, photo paste, STS draft PDF, Excel numbers, shared limits.  
**Next ship:** A23 typed-phrase Forget (after A22 implemented).  
**Not promised:** OneDrive Excel robot, canvas editor, Users login, folder-delete on Forget, full Comparator suite.
