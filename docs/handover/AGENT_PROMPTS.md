# Agent prompts -- how to keep building after Jian Hong

**Audience:** Eugene, Kevin, vibe-coders, Cursor agents.  
**Date:** 2026-09-11  

Read **[AGENTS.md](../../AGENTS.md)** then **[docs/VIBE_CODE.md](../VIBE_CODE.md)** before any of these. Compulsory skills: `.cursor/skills/ate-prompt/` (`Is it like this?`). AGENTS.md is the map. VIBE_CODE.md is how to edit, check, debug, and add a test (Path A/B/C). This file is paste blocks.

Copy-paste prompts for common jobs also live in [docs/PROMPT_GUIDE.md](../PROMPT_GUIDE.md) (Speak table + PyVISA paste block: grep this repo, never web SCPI). Do not invent a second stack. Live product is `ate/` + worker **8766** + UI **5174**. Ticket ledger: [docs/tickets/INDEX.md](../tickets/INDEX.md).

---

## 1. How to use AGENTS.md (teach this once)

Open it. Stop at the first row that matches the ask.

| I want to... | AGENTS.md row | Do not |
|--------------|---------------|--------|
| Add a person | owners.yaml / Setup Save person | Users folder, SQL |
| Take over a SKU | same Component/Part/Package, your operator, new Version | Copy-replace their workbook |
| Add a Version | Setup Version box + Apply | Excel merge tools |
| Add a SKU we test | inventory.yaml one row | Scrape en.run-ic.com |
| New test | Path B: `register(TestSpec)` + `__init__.py` + measurements. See VIBE_CODE.md | `runner.py`, `main.py`, Path A Save as a new TestSpec |
| Wrap golden | Path C then fill scaffold | Empty wrap DEMO as shipped; paste vendor trees into `ate/` |
| Copy tests | Parked. Enable on Tests page for this Version | Copy Ariff into Eugene; RS0204 ids onto RS1G07 |
| New family | Import family / extra_families.yaml | Edit FAMILY_PACKAGES for extras |
| Photo cell | sheet_map paste.photos | Hardcode A91 |
| Number cell | sheet_map paste.values + campaign_outline.py | Second Excel writer |
| Limits | ate/config/limits + lookup.py | Catalog into #Test_Database |
| UI tab | index.html + app.js + UI_CONTRACT | Fourth webfont, second nav |

Blast radius (if they edit these, they break everyone): `database.py`, `runner.py`, `registry.py`, `worker/server.py`, `ate/ui/web/*`.

After worker-loaded code: `restart_ate_worker.bat` when idle. After UI: Ctrl+F5.

Every non-trivial change: run the **matching** check in AGENTS.md Checks. A green check that could never fail is not a check.

---

## 2. How to prompt an agent (every time)

Prefix every Cursor chat with:

```
Live product is ate/ + worker 8766 + UI 5174. Read AGENTS.md then docs/VIBE_CODE.md. Compulsory skills: .cursor/skills/ate-prompt, ate-add-test, ate-ocr, ponytail, i-have-adhd. Fill a prompt block, say Is it like this?, then build. Read docs/handover/CLOUD_TEST_DATABASE.md and docs/handover/SOFTWARE_CONSOLE.md if the task touches folders or Excel.
Ponytail full: do not add files that AGENTS.md already covers. Do not edit runner.py / database.py path shape unless I name that file.
Do not unpark A13 / A14. Do not scrape en.run-ic.com into #Test_Database. Do not call input() in TestSpec.run.
Add-test: Path A = this Version catalog; Path B = new TestSpec + measurements; Path C wrap is a scaffold until filled. Do not mix.
OCR/limits: lookup.py text first; PaddleOCR/EasyOCR only if scan + affirmed; Qianfan-OCR / Unlimited-OCR only if named + double confirm; never write #Test_Database.
When done: run the named check (check_add_test if you added a test), idle-restart worker if you touched ate/tests or worker, write docs/subagents_findings/YYYY-MM-DD_<topic>.md, update INDEX.md.
```

Model handoff (repo rule): Plan Grok 4.5 -> Implement Composer 2.5 -> Validate Grok 4.5 high. User picks the model in the UI.

---

## 3. Paste blocks (one job each)

### Add a person

```
Add person <Name>. Write ate/config/owners.yaml via Setup Operator folder + Save person (or Apply campaign). id lowercase ascii, label is the folder. Default this Component/Part/Package as their task. All stays view-only. Do not add a Users folder under #Test_Database. Forget person is yaml only.
```

### Add a part we are testing

```
We are testing <RS622> <package> as <OpAmp|Logic|Level|switch|power>. Add/update ate/config/parts/<key>.yaml (enabled_tests, vcc, fixture_modes). Add one inventory.yaml row only because we test it. Create folders with Setup Create folders + open. Do not scrape en.run-ic.com SKUs into #Test_Database.
```

### Add a test

Path A / B / C -- pick one. Full text: [PROMPT_GUIDE.md](../PROMPT_GUIDE.md).

```
Path B realize test <id> in family <logic> for part <rs1g07>. Create ate/tests/<family>/<id>.py. Import from __init__.py. register(TestSpec). run() power_on_protected + pause_hook, never input(). Return measurements [{id,value,unit}] matching limits specs[].id. Idle-restart worker. Do not edit runner.py. Proof: python -m ate.core.check_add_test then DEMO that id.
```

### Map a new Excel number cell

```
Probe the live campaign xlsx (do not guess). Add paste.values for measurement id <ID> -> cell <CELL> on sheet <SHEET>. Prefer ate/core/campaign_outline.py if this is the RS622-shaped outline; otherwise this Version sheet_map.yaml only. Skip FILL_ME and MergedCell. Do not unpark A13. Do not apply OpAmp golden_layout to Logic. Run python -m ate.core.check_session_values and python -m ate.core.check_campaign_outline.
```

### Datasheet min/max then PASS/FAIL

```
For part <RS622>, put electrical limits in ate/config/limits/<key>.yaml specs: id, unit, min, max, typ, test (TestSpec id). English source is local Downloads/Reference/Reference first, else en.run-ic.com or a PDF I attach. Do not overwrite filled min/max. Never write PDFs into #Test_Database. After START/DEMO, report.json measurements must include min, max, typ, value, result pass|fail|unspec. Export STS datalog.md + html + pdf. Chip x / fail rows only fail when value is outside min/max. typ is display-only.
```

### Cloud DB / new laptop

```
Point this PC at the OneDrive shortcut of #Test_Database. https stays in ate/config/sharepoint.url. START.bat writes the local path into ate/config/cloud_db.txt. Shortcut path can differ (Core AE vs AE FAE nested). Missing folder: console still opens; Setup Choose folder. App zip ATE_APP_ONLY=1 must not mkdir a private DB. Run python -m ate.core.check_cloud_db. Do not unpark A13 Graph.
```

### Pack a new operator zip

```
Rebuild the operator zip with PACK.bat or venv\Scripts\python.exe pack_ate_console.py. Pipeline: .github/workflows/pack-console.yml (push artifact, tag Release). Keep sharepoint.url. Do not embed a private #Test_Database. Run python pack_ate_console.py --check. Tell operators: Add shortcut to OneDrive (not Sync), START.bat, Choose folder if missing, Ctrl+F5 if UI changed.
```

### After a failed run

```
Open this campaign sessions/datalog.md and datalog.pdf. List every result=FAIL with value vs min/max. Do not delete Version folders. Do not stamp the lab xlsx as PASS for DEMO.
```

### OpAmp noise (do not "fix" it into nV/rtHz)

```
For RS622 noise: keep ate/tests/opa/noise.py (0.1-10 Hz Vpp / gain). Do not fake EN_1kHz from that capture. Do not call input(). Do not AUToscale.
```

### VoS modular fixture (research, not a rewrite)

```
Read docs/handover/VOS_RESEARCH.md. Keep vos_sweep TestSpec (G201/G1001 research fixture). Do not move research writes into someone else's lab Version. Do not call input(). Propose board interconnect only; do not invent a second console or unpark A13.
```

### Ship leftover A20 honesty only

```
Wave: A20 leftover only. RS2323 rON min/max is still a PDF image -- do not fake a table extract. Do not scrape RUN-IC catalog. Do not touch A13/A14. Run python -m ate.core.check_specs_datalog and python -m ate.core.check_lookup. Update STATUS.md if a real extract lands.
```

### Independent verify (no code)

```
V07 R-0003. For epic A07 (then A08..) read the epic acceptance, run the named check, click or RPC the buyer path once, write docs/subagents_findings/YYYY-MM-DD_aXX-r0003-verify.md PASS or FAIL. Do not reopen tickets to improve everything.
```

---

## 4. Customization menu (what is left to build)

Allowed next (founder asks first except leftover honesty):

1. More `paste.values` corners after probing a live xlsx (Logic VCC grid, RS0204 Icc).
2. Limits yaml for every inventory part that still has `unspec`.
3. Wrap remaining goldens that do not call `input()`.
4. New person / Version / SKU via Setup (no agent required).
5. Extra family via Import family.

Parked until founder unparks:

- A13 OneDrive Excel MCP
- A14 xyflow
- No-code test wizard
- ML trainer
- Delete dual-stack `main.py`
- Full Comparator / Interface / Vref / Clock / Data conversion suites
- Cloud-hosted worker (VISA is on the desk)

---

## 5. Proof commands (run the layer you touched)

```
python -m ate.core.check_cloud_db
python -m ate.core.check_new_product
python -m ate.core.check_operator_tree
python -m ate.core.check_ui_contract
python -m ate.core.check_family_load
python -m ate.core.check_add_test
python -m ate.core.check_demo_families
python -m ate.core.check_campaign_outline
python -m ate.core.check_session_values
python -m ate.core.check_specs_datalog
python -m ate.core.check_lookup
python -m ate.core.check_tags_datalog
python -m ate.core.check_sync_repo
python pack_ate_console.py --check
```

Idle worker restart: `restart_ate_worker.bat`.
