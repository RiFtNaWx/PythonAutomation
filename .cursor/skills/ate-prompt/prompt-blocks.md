# Paste blocks (fill then `Is it like this?`)

Live product is `ate/` + worker **8766** + UI **5174**. Copy a block, fill `<>`, then affirm.

## Vibe-code / debug (every code chat)

```
Live product is ate/ + worker 8766 + UI 5174. Read AGENTS.md then docs/VIBE_CODE.md.
Compulsory skills: .cursor/skills/ate-prompt, ate-add-test, ate-ocr, ponytail, i-have-adhd.
Ponytail full: do not add files that AGENTS.md already covers. Do not edit runner.py / database.py path shape unless I name that file.
Do not unpark A13. A14 Recipe canvas is live (closed opcodes; no eval). Do not scrape en.run-ic.com into #Test_Database. Do not call input() in TestSpec.run.
Add-test: Path A = this Version catalog; Path B = new TestSpec + measurements; Path C = remember + trigger original file:line (no new imported_*.py). Do not mix.
When done: run the named check, idle-restart worker if you touched ate/tests or worker, write docs/subagents_findings/YYYY-MM-DD_<topic>.md, update INDEX.md.
```

## Path A -- customize this Version (no Python)

```
On this campaign only, enable existing TestSpec ids <id,...> via Tests page Save this Version. Write _manifest/test_catalog.yaml enabled_tests. Catalog wins over parts yaml. Do not edit ate/config/parts unless I want every operator of this SKU. Do not invent a TestSpec. Do not copy another person's catalog.
```

## Path B -- realize a new test

```
Path B realize test <id> in family <opamp|logic|switch|power> for part <rs1g07>. Create ate/tests/<family>/<id>.py. Import it from that package __init__.py. register(TestSpec) with id, label, required_instruments, fixture_mode, lab_sheet, run, dual_channel=False unless CHA/CHB probe move is required. run() must use power_on_protected and params.pause_hook, never input(), never import Lim.* / Ariff.*. Return measurements [{id, value, unit}] whose id matches ate/config/limits/<part>.yaml specs[].id. Add id to parts/<key>.yaml enabled_tests. Idle-restart worker. Map excel_sheet in this campaign sheet_map.yaml if a workbook sheet exists (probe cells, do not guess). Do not edit runner.py. Proof: python -m ate.core.check_add_test then DEMO that id.
```

## Path C -- remember + trigger

```
Path C remember def test_<name> from <golden file> into family <logic> for this campaign. Tests page Remember + enable on this Version. Stores file:line in snippet_map.yaml and START triggers that function. Do not rewrite the golden. Do not write imported_<id>.py. Block if input() or Lim/Ariff/Soo. Vendor goldens stay Path B in ate/tests. Do not edit runner.py.
```

## Person

```
Add person <Name>. Write ate/config/owners.yaml via Setup Operator folder + Save person (or Apply campaign). id lowercase ascii, label is the folder. Default this Component/Part/Package as their task. All stays view-only. Do not add a Users folder under #Test_Database. Forget person is yaml only.
```

## Part we are testing

```
We are testing <RS622> <package> as <OpAmp|Logic|Level|switch|power>. Add/update ate/config/parts/<key>.yaml (enabled_tests, vcc, fixture_modes). Add one inventory.yaml row only because we test it. Create folders with Setup Create folders + open. Do not scrape en.run-ic.com SKUs into #Test_Database.
```

## Limits / datasheet / OCR

```
For part <RS622>, ingest the datasheet: python -m ate.core.ingest_datasheet <RS622> --pdf <optional> --xlsx <optional>. Local PDF text first; cloud HTML for this SKU if thin; PaddleOCR autodownload only if still thin. Write ate/config/limits/<key>.yaml (specs SoT). Truth table SoT stays ate/config/parts/<key>.yaml. Export ate/config/datasheets/tables/<key>.json (JSON, not XML). Store xlsx as a relative key under reports_root or #Test_Database/_ate/goldens. Slice any prefix at #Test_Database (ate.core.paths.PATH_RULE). Fill golden *_filled.xlsx (source xlsx stays). Sweep rows -> Sweep sheet + sessions/sweep_summary.md. Do not guess A91. Never write PDFs into #Test_Database. Never commit C:\Users\<name> into coverage.json.
```

## SCPI / instruments (grep this repo)

```
Translate what I said into this repo only. Golden SCPI lives in psu_setup.py (DP832 power_on_protected), generator_setup.py (DG822 Pro APPL SQU/DC, OUTP, LOAD INF), dmm_setup.py (DMM6500 :CONF + :READ?, never *RST, never NPLC/AZER/AVER/TRAC), scope_setup.py (MSO5072). Call those helpers from ate/tests/<family>/. Never invent a header. Rigol -116 / DMM6500 -113 = delete the write. IDD OVP is 5.6 V not 5.5. Do not search online for SCPI.
```

## Excel number / photo

```
Probe the live campaign xlsx (do not guess). Add paste.values for measurement id <ID> -> cell <CELL> on sheet <SHEET>. Skip FILL_ME and MergedCell. Do not hardcode A91. Do not unpark A13. Run python -m ate.core.check_session_values and python -m ate.core.check_campaign_outline.
```

## After a failed run

```
Open this campaign sessions/datalog.md and datalog.pdf. List every result=FAIL with value vs min/max. Also read sessions/run_log.txt and report.json measurements. Name the cause (limits miss, missing instrument, catalog hid the test, scaffold wrap, VISA). Do not delete Version folders. Do not stamp the lab xlsx as PASS for DEMO.
```
