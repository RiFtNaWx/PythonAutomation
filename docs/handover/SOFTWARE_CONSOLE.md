# Software -- operator console + Excel (handover row 1)

**Audience:** Eugene (founding), AE, Design.  
**Date:** 2026-09-11  
**One sentence:** One console on the laptop. Four tabs. Results and Excel live in `#Test_Database`. Autofill is `sheet_map` cells, not a second Excel product.

Companion: [CLOUD_TEST_DATABASE.md](CLOUD_TEST_DATABASE.md), [AGENT_PROMPTS.md](AGENT_PROMPTS.md), [AGENTS.md](../../AGENTS.md), [STATUS.md](../../STATUS.md), [docs/SHIP_NEXT.md](../SHIP_NEXT.md).

---

## 1. What shipped (say this)

"One program on the laptop. Four tabs: Setup, Run, Results, Tags.

Pick your name, click Apply, then run. Excel fills from the result file. You don't type the numbers.

All is look-only. Don't share someone else's folder."

Live stack: `ate/` + worker **8766** + UI **5174**.  
Legacy: `main.py` / `opa_tests.py` -- golden source only. Console does not see a `test_*` until Wrap / `register(TestSpec)`.

Done that AE can see:

1. Family rail: OpAmp / Logic / Analog switch / Level (Level is a stub suite).
2. People folders. Add person from Setup, no Python.
3. Tags, run ledger, living `report.json` merge, STS datalog PDF.
4. Photo paste into Excel (`paste.photos`).
5. Number paste into Excel (`paste.values`) on session end or Results **Fill Excel numbers**.
6. Datasheet limits from local `Downloads/Reference/Reference` first, then `ate/config/limits/<part>.yaml`. Website only if that SKU has no local PDF.

Git / zip: [README.md](../../README.md). UI chrome must stay: [ate/ui/web/UI_CONTRACT.md](../../ate/ui/web/UI_CONTRACT.md).

---

## 2. How to launch (two audiences)

| Who | How | Do not |
|-----|-----|--------|
| AE / operator | Unzip, Add shortcut to OneDrive, `START.bat` | Edit Python; private DB in unzip; SharePoint Sync |
| Engineer | `START.bat` after clone (or `run_ate_app.bat` if venv exists) | Start work in `main.py` |

After **code** the worker loads (`ate/tests/**`, `runner.py`, worker, `opa_tests.py`): idle-restart `restart_ate_worker.bat`. Not mid-run.  
After **UI-only**: Ctrl+F5. Restart worker only if an RPC was added.

Ports: **8766** worker, **5174** UI. Never 8765 / 3000 / 3001 / 5000.

---

## 3. Console -- what each section is, and what to say

Four tabs only. Do not add a fifth.

### Header (always visible)

| Control | What it does | Say |
|---------|--------------|-----|
| Family rail (left) | Loads that family's tests | "This is product class, not a person." |
| Operator (top-right) | Jumps to that person's campaign | "Pick your name. All is look-only." |
| READY / STOP | Session state / abort | "STOP parks instruments. Do not kill Excel instead." |
| Pin-1 hint (Setup) | Orientation gate | "Wrong pin-1 = Abort, rotate, Continue." |

### Setup tab -- Test Database

Walk top to bottom. Combos: click box or caret, type to add, x to clear. Changing a combo does **not** Apply. Click **Apply campaign**.

| Control | Say | Do |
|---------|-----|-----|
| Component / Part / Package | "These are the SharePoint folders." | Pick existing, or type a new SKU then Create folders |
| Operator folder | "Person name = folder name." | Type Jane -> **Save person** or Apply. Forget person drops yaml only |
| Version | "Version_1 is a campaign, not the year." | Type Version_2 + Apply to start a new tree for *this* person |
| Model / Year | Meta on the campaign | Optional |
| Tags | Space or Enter adds a chip | Full editor is the Tags tab |
| Kind / Value / Scope | Extra labels (board rev, lot) | Scope: this campaign / this class / all products |
| **Apply campaign** | "This is the commit." | Required before Discover / START |
| Open DB folder | Explorer to this Version | Confirm you are not in someone else's tree |
| Open sessions | `sessions/` | JSON + STS files |
| **Open central DB** | Root `#Test_Database` or SharePoint https | If folder missing: sync OneDrive, fill `cloud_db.txt` |
| Import xlsx | Copies into `workbook/` + outline `sheet_map` | Blank path = file picker. Filled maps are not overwritten with FILL_ME |
| Import family | Extra family Python into `ate/tests/<key>/` | Never `opamp`/`logic`/`level`. See ATE_PLUGIN.md |
| Tracking sheet / Create folders + open | New SKU we are actually testing | One inventory row. Do not dump RUN-IC homepage |
| Detected tests / Wrap / Copy | Ingest golden `test_*` | AST only. Blocks `input()`. Copy = same family only |

PSU safety hint: OVP/OCP always on (Vset+0.3 V, Iset+0.1 A). Not DP832 30 V / 3 A.

### Setup tab -- Session (right column)

| Button | Say |
|--------|-----|
| Discover | "Finds MSO / PSU / AWG / DMM by `*IDN?`. No hardcoded USB." |
| Open Session | "START stays grey until this succeeds." |
| Screenshot / Open Screenshots | Manual capture into campaign folders |
| + Session | Writes `session_*.json` without running tests |

### Run tab

| Block | Say |
|-------|-----|
| DUT / Channel | "Category-first: board, then channel, then DUT. Continue between gates." |
| Run conditions | Family-local knobs (Logic does not show G11). From `param_defaults` |
| Board gains | Locked YAML for OpAmp fixtures. Not a free gain dial |
| Test program | Checkboxes = `enabled_tests` for this part |
| START | Live USB instruments. Writes JSON + STS PDF + live xlsx numbers |
| DEMO (SIM) | Fake PyVISA, same START path. STS PDF is the report. Excel goes to `*_demo.xlsx`. Continue is auto. |

### Results tab

| Block | Say |
|-------|-----|
| Run ledger | Who ran what. This campaign / this SKU / all. Chip x deletes one JSON, not the Version |
| Last results | Living `report.json` view |
| Export STS datalog | md + html + pdf |
| **Fill Excel numbers** | `paste.values` from living JSON. Use if xlsx was closed during session end |
| Fetch limits | Local Reference PDF first, then website for *this* SKU only |
| Waveform layout | Photo boxes. Save writes `sheet_map` `paste.photos`. Do not hardcode A91 in Python |

### Tags tab

Campaign tags, board tags, import/filter. **Clear all tags** empties yaml + TAGS.txt. Does not delete folders.

---

## 4. Excel -- precise cells (autofill)

There is **one** Excel writer: `ate/reporting/lab_report.py` + `session_paste.py` (photos) + `session_values.py` (numbers).  
Map file: campaign `_manifest/sheet_map.yaml`.  
Known cells (do not invent new ones in Python): `ate/core/campaign_outline.py`.

Import / Create folders builds the outline (folder, sheet, fixture_mode). It does **not** write FILL_ME. Photos attach only when the layout is the Eugene TTSOP8 8-box golden.

### 4.1 Operator recipe (what to do in Excel)

1. Close the xlsx **or** expect a `{stem}_filled.xlsx` if Excel has the file locked.
2. Apply the right campaign (person + Version).
3. START or DEMO the tests that have measurements.
4. Session end fills mapped cells. If not: Results -> **Fill Excel numbers**.
5. Open the campaign `workbook/*.xlsx`. Check the sheet named in `excel_sheet` (GBW, VOS, VOX, ICC, Iplus, ...).
6. Photos: Results Waveform layout if a box is wrong; Save layout. Do not ask an agent to "put A91 in lab_report.py".

DEMO must not be sold as datasheet PASS.

### 4.2 Mapped numbers (as of 2026-09-11)

| Family | Part / book | Sheet | Measurement id | Cells | Notes |
|--------|-------------|-------|----------------|-------|-------|
| OpAmp | RS622 TTSOP8 | GBW | GBW_MHz | CHA R20:U20, CHB AA20:AD20 | DUT columns |
| OpAmp | RS622 TTSOP8 | GBW | F_3dB_kHz | R19:U19 / AA19:AD19 | |
| OpAmp | RS622 TTSOP8 | GBW | VOUT_1k_mV | R17:U17 / AA17:AD17 | |
| OpAmp | RS622 TTSOP8 | VOS | VOS_mV | R16:U16 / AA16:AD16 | |
| OpAmp | RS622 TTSOP8 | Noise | VN_OUT_PP_mV | R16:U16 (see live sheet_map) | 0.1-10 Hz Vpp, **not** nV/rtHz |
| OpAmp | RS622 SOP8 | GBW | GBW_MHz | CHA C21:E21, CHB J21:L21 | Skip golden merge if cells already have numbers |
| OpAmp | RS622 SOP8 | VOS | VOS_mV | B16:E16 / I16:L16 | |
| Logic | RS1G08-class VOX | VOX | VOH_4p5V | G16, H16, I16 | Overlapping 4.5 V cells only |
| Logic | | VOX | VOL_4p5V | G25, H25, I25 | |
| Logic | | ICC | ICC_uA | D10 | |
| Switch | RS2323 Iplus | Iplus | IPLUS_uA | B2 | |

ORT: **photos only**. Do not invent recovery-time numbers.

RS0204 Icc / VOH condition grids: **unmapped**. Do not fake them.

Merged cells: fill skips. Tracking xlsx that already has GBW/VOS numbers does not get OpAmp golden merge-center (that turned C21 into MergedCell).

### 4.3 Mapped photos (merged boxes, not hardcoded cells)

Photo paste reads campaign `sheet_map` `paste.photos`, which is **discovered** from the live xlsx:

- Each box is a merged 4-col x 10-row block (A/E/I/M... same size as Eugene TTSOP).
- Anchor = top-left of that merge, after Test Conclusion (intro wrap sets the row).
- Horizontal: one CHA/CHB pair per DUT (`sample_size`).
- Vertical: one band per trial (Slew 1VPP/2VPP/POS/NEG; ORT POS then NEG). Extra bands are `t2_` / `t3_`.
- Do not copy a snapshot like A70/A45 onto another package. Do not re-run golden insert on a filled book.

Change a box: Results -> Waveform layout -> Save, or re-discover from merges. YAML only.

### 4.4 How to add a new Excel cell (engineer)

1. Open the live xlsx, note sheet name + cell (probe, do not guess).
2. Put it in `campaign_outline.py` if it should apply to every RS622-shaped campaign, **or** in this Version's `sheet_map.yaml` `tests.<key>.paste.values`.
3. Test `run()` must return `measurements: [{id, value, unit}]` with that **id**.
4. `python -m ate.core.check_session_values` and `python -m ate.core.check_campaign_outline`.
5. Do not invent FILL_ME. Do not unpark A13.

YAML shape:

```yaml
tests:
  gbw:
    excel_sheet: GBW
    folder: GBW
    paste:
      photos:
        u1_chA: A10   # top-left of the merged 4x10 box; not a hardcoded A45
      values:
        GBW_MHz:
          CHA: [R20, S20, T20, U20]
          CHB: [AA20, AB20, AC20, AD20]
```

---

## 5. Daily operator flow (one page)

1. Pick **you** (not All). Apply campaign.
2. Discover -> Open Session.
3. Confirm pin-1. Tick tests. START or DEMO.
4. Continue through DUT / channel gates. SAFE IDLE turns AWG then PSU off while waiting.
5. Close Excel if you need the same file written. Or use Fill Excel numbers.
6. Results: Export STS if you need a printable P/F sheet. Fetch limits if min/max are blank.
7. OneDrive syncs. The other laptop sees it after sync -- not instantly in RAM.

---

## 6. Not finished (software row)

Must (buyer-visible):

1. Logic fill is not every VCC corner. RS0204 grids unmapped. ORT no fake us.
2. RS2323 rON min/max still a PDF **image**. Banner typ 0.6 + IPLUS max 1.
3. Stub RUN-IC classes: Comparator, Interface, Vref, Data conversion, Clock (`live: false`).
4. OpAmp PSRR / CMRR / AOL / EMIRR / PowerOn are mapped captures. Noise is 0.1-10 Hz Vpp, not nV/rtHz.
5. Independent R-0003 verify still pending on A07-A12.

Parked: A13 Excel MCP, A14 xyflow, no-code wizard, ML trainer, delete `main.py`, scrape en.run-ic.com.

Next waves (do in order): leftover A20 honesty (rON image), V07 verify, then founder-asked stub suites. A19/A21 already implemented. Print [docs/SHIP_NEXT.md](../SHIP_NEXT.md).

---

## 7. Design prompts (paste into Cursor / a designer)

Use these when someone asks "make a slide / poster / AE one-pager". They are **prompts**, not a second product.

### Prompt -- AE one-pager

```
Design a one-page A4 landscape for AE + Design. Title: ATE operator console.
Four boxes: Setup, Run, Results, Tags. Footnote: laptop runs the app; #Test_Database on SharePoint holds results.
Do not invent a fifth tab. Do not show a cloud Python server. Ports 8766 / 5174 only as small footer.
Reference: docs/handover/SOFTWARE_CONSOLE.md section 3 and ate/ui/web/UI_CONTRACT.md (Barlow / JetBrains Mono / Space Grotesk).
```

### Prompt -- Excel autofill diagram

```
Draw a left-to-right flow: START -> sessions/report.json (merge by test+DUT) -> sheet_map paste.values -> workbook xlsx cell.
Call out: photos = paste.photos; numbers = paste.values; locked xlsx -> *_filled.xlsx.
Cells table from docs/handover/SOFTWARE_CONSOLE.md section 4.2. Do not draw Graph API.
```

### Prompt -- do-not poster for vibe-coders

```
Six red rules, one line each: no runner.py for new tests; no database.py path rewrite; no main.py; no input(); no Lim.* import; no Tags/Users folder under #Test_Database.
Green path: AGENTS.md table "Where to change".
```

UI implementation still follows UI_CONTRACT. Do not "modernize" the left rail.

---

## 8. Where to refer (do not re-derive)

| Need | File |
|------|------|
| Where to edit | [AGENTS.md](../../AGENTS.md) |
| Add test / family slots | [docs/ATE_PLUGIN.md](../ATE_PLUGIN.md) |
| Paste-one-block prompts | [docs/PROMPT_GUIDE.md](../PROMPT_GUIDE.md) |
| Tabs / fonts | [ate/ui/web/UI_CONTRACT.md](../../ate/ui/web/UI_CONTRACT.md) |
| Done / not done | [STATUS.md](../../STATUS.md) |
| Next epic order | [docs/SHIP_NEXT.md](../SHIP_NEXT.md) |
| Outline / known cells | `ate/core/campaign_outline.py` |
| Fill numbers | `ate/reporting/session_values.py` |
| Fill photos | `ate/reporting/session_paste.py` + `photo_layout.py` |
| PRD | [docs/prd/PRD-001-ate-multi-product-platform.md](../prd/PRD-001-ate-multi-product-platform.md) |
