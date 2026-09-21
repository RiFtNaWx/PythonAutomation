# ATE agent + vibe-coder guide (PythonAutomation)

Read this before editing the operator console, adding a person, or adding a product family. Same system prompt: `CLAUDE.md` and `AI.md`. Agents must read this file first. Do not ask anyone to paste a Copilot block.

**Compulsory Cursor skills** (clone-installed, auto-use, do not skip): `.cursor/skills/ate-prompt/`, `ate-add-test`, `ate-ocr`, `ponytail`, `i-have-adhd`. Rule: `.cursor/rules/ate-skills-compulsory.mdc`.

This repo has two stacks. **The live product is the operator console** (`ate/` + worker **8766** + UI **5174**). Root `main.py` / `opa_tests.py` / `logic_tests.py` is the **legacy dual-stack**. Do not start a new test, user, or campaign there. Golden bodies may be copied *from* those files into `ate/tests/<family>/` via Setup Detect/Wrap -- that is ingest, not a second runtime.

Two ways to get the console (same `START.bat` in both):

| Who | What they get | Database |
|-----|---------------|----------|
| **App user** | Zip from `pack_ate_console.py`, double-click `START.bat` | Same OneDrive shortcut of `#Test_Database` (`cloud_db.txt`) |
| **Vibe-coder** | `git clone -b eugene-console` this repo, double-click `START.bat` | Same folder. Do not invent a private unzip copy |
| **Vibe-coder** | `git clone -b eugene-console` this repo, read this file | Same folder. Do not invent a private unzip copy |

Paste the SharePoint *https* link into `ate/config/sharepoint.url` when you have it. Each PC still needs the *local OneDrive path* in `cloud_db.txt` (Windows cannot treat the https URL as a folder). Shortcut layouts differ by Add-shortcut date; START discovers them. If the folder is missing, START still opens the console -- Setup **Choose folder**. A13 Graph stays parked. START/DEMO write `sessions/` + Excel paste into that folder; OneDrive uploads. No second cloud writer.

Daily clone update: `python -m ate.core.sync_repo` (Cursor folder-open + `run_ate_app.bat`). `git pull --ff-only` only when the tree is clean. Dirty tree = fetch only. Never `reset --hard`.

How to edit / debug / add a test (three paths): `docs/VIBE_CODE.md`. How to specify the prompt: `.cursor/skills/ate-prompt/`. Longer plug-in detail: `docs/ATE_PLUGIN.md`. UI chrome: `ate/ui/web/UI_CONTRACT.md`. Human landing: `README.md`. Ticket ledger: `docs/tickets/INDEX.md`.

## Mental model (do not invent a fourth axis)

| Word | What it is | What it is not |
|------|------------|----------------|
| Family | Left rail: `opamp` / `logic` / `switch` / `level` (+ extras) | A person. `lim` is an alias for analog switch |
| Operator | A person folder under the campaign (`Eugene`, `Ariff`, ...) | A family. Top-right **All** is view-only |
| Campaign | One Version tree with workbook + sessions | A website SKU dump |
| Tracking row | `ate/config/inventory.yaml` (what we test now) | RUN-IC homepage catalog |

**Same project, different people** is already the database shape:

```
#Test_Database/{Component}/{Part}/{Package}/{Operator}/{Version_N}/
```

Example: ChangThong and Ariff both run RS1G08 SC70-5. That is two operator folders under the same part/package, not a fork of the repo and not a Users table.

```
#Test_Database/Logic/RS1G08/SC70-5/Ariff/Version_1
#Test_Database/Logic/RS1G08/SC70-5/ChangThong/Version_1
```

Each person gets their own `_manifest/`, `workbook/`, `sessions/`. Do not overwrite someone else's Version folder. Do not add `Tags` or `Users` as a path segment. Tags live in `_manifest/tags.yaml` + campaign-root `TAGS.txt`.

## Where to change (stop at the first row that holds)

| I want to... | Touch these | Do not touch |
|--------------|-------------|--------------|
| Add a **person** (new operator) | Setup **Add person** (default: **this campaign SKU only**). People self-register: first-run name + Continue, then Results **Pick up**. Settings **All SKUs + golden** is the explicit dump (`all_skus=True`). Do not dump `inventory.yaml` onto a new person. `owners.yaml` then pick that person (not All). | `database.py` path shape; a SQL users table; family rail; `runner.py` |
| Golden lab book per SKU | `python -m ate.core.golden_refs` extracts lab xlsx from `Test Reports.zip` into `%USERPROFILE%/Downloads/Product Testing Report` (`inventory.yaml` `reports_root`, env-expanded). Copies that drop into `#Test_Database/_ate/goldens`. Zip users: resolve `#Test_Database` from any OneDrive prefix (`ate.core.paths.PATH_RULE`). Store `report:` as a relative key (`RS622/foo.xlsx`), never `C:\\Users\\<name>`. Provision copies the ref into this operator `workbook/`. Probe `sheet_map` from **that** book. | One Parameter/DUT table; OpAmp golden on Logic VIX; copy `sessions/`; invent A91; scrape en.run-ic.com; committing Jianhong absolute xlsx into `coverage.json` |
| Datasheet min/max | Recipe: [docs/datasheet/INGEST.md](docs/datasheet/INGEST.md). Specs SoT `ate/config/limits/<key>.yaml`. Truth table SoT `ate/config/parts/<key>.yaml`. Export index `ate/config/datasheets/tables/<key>.json` (JSON not XML). PDFs: `%USERPROFILE%/Downloads/Reference/Reference` else `#Test_Database/Reference`. Ingest: `python -m ate.core.ingest_datasheet PART --pdf <file> --xlsx <file>`. `coverage.json` stores relative `xlsx` + `path_rule`. | Catalog scrape into `#Test_Database`; paste-copilot; guess A91; XML table dump; absolute `C:\\Users\\` in zip config |
| Take over a product already in the DB | Same Component/Part/Package. Switch operator to yourself. Type a new Version_N in the Version box then Apply | Copy-replace the other person's `workbook/` or `sessions/` |
| Add a **Version** | Setup Version box (pick or type, same as labels). Apply campaign runs `ensure_version`. Copies `_manifest` stubs from the current version if missing; does not clone xlsx | Excel merge tools; a second campaign root |
| Add a SKU we are testing | One row in `ate/config/inventory.yaml` (part + model + package + lot). RS0204 stays `category: level` + `ate_suite: logic`. Do not scrape en.run-ic.com | `run_ic.yaml` homepage SKUs (RS724-Q1 ...) |
| New part defaults / enabled tests | `ate/config/parts/<key>.yaml` | `runner.py` import lists |
| New **test** in an existing family | Path B in `docs/VIBE_CODE.md`: `register(TestSpec)` in `ate/tests/<family>/` + `__init__.py` import + `measurements` + part `enabled_tests` + limits id match. Restart worker | `main.py`, `runner.py`, `input()`, `import Lim.*` / `import Ariff.*`; treating Tests-page Save as a new TestSpec |
| Customize which tests **this Version** shows | Tests page **Save this Version** -> `_manifest/test_catalog.yaml` (catalog wins over part yaml) | Shared `parts/*.yaml` unless you mean every operator of that SKU |
| Per-test sweep / specs **this Version** | Test program **Parameters** + **Write** -> `_manifest/test_params.yaml`. START sends `test_params`; `RunParams.overlay_for(test_id)` applies them. | Shared Setup Run-conditions VCC dropdown; editing every test body |
| Wrap a golden `test_*` | Path C: Tests page Remember + enable. Scan stores `file:line` in `snippet_map.yaml` and START triggers that function. Does **not** rewrite the golden or write a new `imported_<id>.py`. Blocked if `input()` or `Lim`/`Ariff`/`Soo`. Vendor goldens stay Path B in `ate/tests/`. A16 leftover `imported_input_off_leakage.py` may still exist. | Pasting vendor trees into `ate/`; wrapping into another family; treating leftover scaffold DEMO as realization |
| Compile / browse author goldens | `goldens/` byte copies. Tutorial: [goldens/TUTORIAL.md](goldens/TUTORIAL.md). Refresh: `UPDATE_GOLDENS.bat` or `python -m ate.core.golden_gateway --import --verify`. Push: `push.bat` (gateway blocks mixed goldens + `runner.py`). | Pasting those trees into `ate/tests/`; rewriting `time.sleep`; a second ATE runtime; mixing goldens and blast-radius in one commit |
| Copy tests to another person or part | Parked. Enable / add on Tests page for **this** operator Version. Same family only. Fill gaps from **this person's** other Versions | Copy Ariff into Eugene; RS0204 dual-rail ids onto RS1G07 |
| New **family** | Setup Import family, or `ate/tests/<family>/` + `ate/config/extra_families.yaml` | Editing `FAMILY_PACKAGES` in `registry.py` (built-ins only). Never ingest into `opamp`/`logic`/`level` |
| RUN-IC class / stub suite | `ate/config/run_ic.yaml` (`live: false` until a suite exists) | Pointing Power/Comparator at OpAmp |
| Photo cell in Excel | Campaign `_manifest/sheet_map.yaml` `tests.<key>.paste.photos` -- discovered from merged 4-col DUT boxes or 8-col CHA/CHB pairs on the live xlsx (intro length + DUT count + trial bands). Two boxes on a row = Channel A then Channel B (OpAmp Slew golden). | Hardcoded A91/A70 in Python; a second Excel writer; golden insert on a filled book |
| Numeric cell in Excel | Campaign `sheet_map.yaml` `tests.<key>.paste.values` (id -> cell, DUT list, or CHA/CHB grid). Known cells live in `ate/core/campaign_outline.py` (probed, not hardcoded: VOX unique Vcc DUT rows, ICC `maximum (uA)` cell, Iplus B2, GBW R20 or C21). Results -> Fill Excel numbers | Inventing cells; FILL_ME stubs; OpAmp golden on Logic; aliasing VOX 1.65V as `VOH_2p0V` |
| Intro text / datasheet / conclusion | Campaign `sheet_map.yaml` `tests.<key>.paste.narrative` (probed Test Conditions / Circuitry / Datasheet / Test Conclusion B cells). Fill Excel writes those on `*_filled.xlsx` from limits yaml + fixture checklist. `#VALUE!` cleared. Excel comments mark paste cells. Lab book comes from a senior or an AI agent annotating the OpAmp golden. STS PDF is the research log. | Inventing a research-report format; overwriting senior text that is already real; OpAmp `layout_rules` on Logic |
| Probe CHA/CHB | Setup Channel A/B ticks. Defaults: OpAmp A+B, Logic/switch/level/power A. Saved on this Version in `_manifest/run_prefs.yaml`. Optional part yaml `channels:` is only the default. | Forcing yaml per SKU; scraping en.run-ic.com for pin count |
| DUT count | Setup **DUT count** (1-16) + tick which sockets to run. Saved `run_prefs.sample_size`. STS PDF lists the DUTs / channels / tests that ran. | Hardcoding 4 DUTs; editing `parts/*.yaml` sample_size for each campaign |
| Paste / golden layout | `ate/reporting/lab_report.py` + `session_paste.py` / `golden_layout.py` | Unparking A13 OneDrive MCP |
| Operator UI page / tab | `ate/ui/web/index.html` + `app.js` + `styles.css` per `UI_CONTRACT.md`. Bump `?v=` | Second nav, fourth webfont, new CSS framework |
| PSU on | `power_on_protected` only | DP832 30 V / 3 A; unprotected `power_on` |
| Instruments / VISA | `ate/instruments/` + existing `*_setup.py` helpers | Rewriting PyVISA as a new stack |
| Tags / STS datalog | `ate/core/tags.py`, `datalog.py` | Tags folder under `#Test_Database` |
| Living latest JSON / merge | `ate/core/datalog.py` `sync_report_from_session` -- merge by test_id+dut(+channel); keep tests not run this START | Wipe `report.json`; share one latest file across operators |
| Per-test history records | `{test_key}/DUT_n/records/{test_id}_{timestamp}.json` via `write_step_record` | Tags/Users path axis; overwriting history files |
| See who ran what / delete a session JSON | Results -> Run ledger (`list_runs`). Chip `x` or Tags -> Clear all tags | Deleting Version folders; unparking A13 SharePoint MCP |
| Lab progress board / first-run name | Results `#panel-progress-board` (who's working, PIC, no-PIC pickup, register); `#Test_Database/_ate`; Kevin observer | Password login; Users table; hiding files; GitHub issues from the zip |
| Point the lab at a shared cloud folder | `ate/config/sharepoint.url` (https) + each PC `ate/config/cloud_db.txt` (OneDrive path). Shortcut path can differ (Core AE vs AE FAE nested). Missing folder: console still opens; Setup **Choose folder**. `bench.yaml` `test_database_root` still works on this bench | A second Excel writer / Graph API / A13 / a private `#Test_Database` inside the app zip; blocking START |
| Daily git update (clone PCs) | `ate/core/sync_repo.py` -- ff-only, skip if dirty | `git reset --hard`; stash-on-open; merge that can clobber edits |

Worker JSON-RPC surface: `ate/worker/server.py`. Add a method only when Setup/Run already cannot do the job via yaml + existing RPC (`ensure_product`, `ensure_version`, `list_owners`, `import_family`, ...).

## Add a person (copy this)

1. Setup **Operator folder**: type the person's name (folder name on disk). **Save person** or **Apply campaign**. That writes `ate/config/owners.yaml` (`id` lowercase ascii, `label` = folder). Current Component/Part/Package is their default + `task`.
2. Pick that person (not All). **Create folders + open** or Apply so `#Test_Database/.../{TheirLabel}/Version_1` exists.
3. `parts:` is their default picker list, not an ACL. Other people can still open the same part.
4. Do not add `id: all` clones. **All** stays view-only. **Forget person** is Settings: type `FORGET {label}`. Yaml row drops; Version folders stay unless wipe is ticked (this person's trees only).
5. Agents may still append yaml by hand; the console path is the operator path.

```yaml
  - id: jane
    label: Jane
    default_family: logic
    default_part: rs1g08
    default_component: Logic
    default_package: SC70-5
    parts: [rs1g08]
    task: RS1G08
```

Then Jane's tree is `Logic/RS1G08/SC70-5/Jane/Version_1`. Ariff's tree next to it is untouched.

`inventory.yaml` `pic:` is the tracking-sheet owner. It does not lock the part. Empty pic must not clobber another SKU of the same part (see `migrate_operator_folders._pic_label_map`).

## Add a test (three paths -- do not mix)

Full steps, debug table, and worked `cin`/`cpd` example: `docs/VIBE_CODE.md`. Check: `python -m ate.core.check_add_test`.

| Path | Meaning | Done when |
|------|---------|-----------|
| **A Customize** | Tests page Save this Version (`test_catalog.yaml`) | Setup shows an **existing** registry id on this operator Version |
| **B Realize** | New `ate/tests/<family>/<id>.py` + `__init__.py` import + `register(TestSpec)` + `measurements` + part yaml + limits | DEMO that id writes `measurements` `{id,value,unit}` |
| **C Wrap then fill** | Wrap golden `test_*` -> `imported_<id>.py` scaffold | Scaffold is **not** done. Fill like Path B |

```python
# ate/tests/<family>/my_slot.py -- Path B. Import this module from __init__.py
from ate.core.registry import TestSpec, register
from ate.core.runner import RunParams

def run(instr, params: RunParams) -> dict:
    hook = params.pause_hook
    if hook is not None and not hook("My slot: wire PSU CH1, then Continue"):
        return {"summary": "aborted", "data": {}}
    # power_on_protected; never input(); never import Lim.* / Ariff.*
    return {
        "summary": "...",
        "data": {},
        "measurements": [{"id": "MY_uA", "value": 0.8, "unit": "uA"}],
    }

register(TestSpec(
    id="my_slot",
    label="My slot",
    required_instruments=frozenset({"PSU", "DMM"}),
    fixture_mode="LOGIC",  # or BUFFER / G11 / LIM_RS2323 -- family-local
    lab_sheet="MySheet",
    run=run,
    dual_channel=False,
))
```

Shared recipe: add `my_slot` to `ate/config/parts/<key>.yaml` `enabled_tests`. This Version only: Path A after Path B. Limits `specs[].id` must equal `measurements[].id`. Idle-restart worker. Map `excel_sheet` in that campaign `sheet_map.yaml` when a sheet exists. Do not edit `runner.py`.

Copy-paste prompts: `docs/PROMPT_GUIDE.md` (speak -> helpers/SCPI already in this repo; do not paste web SCPI).

## Blast radius (files that break everyone)

| File | If you edit it |
|------|----------------|
| `ate/core/database.py` | Every campaign path on disk |
| `ate/core/runner.py` | Every START / DUT / channel gate |
| `ate/core/registry.py` | Family load for the whole console |
| `ate/worker/server.py` | Every RPC the UI calls |
| `ate/ui/web/*` | Every operator; follow UI_CONTRACT |
| `main.py` / root `*_tests.py` | Legacy only. Console will not see it until wrapped |

Prefer yaml + one `TestSpec` over a clever helper used by all families.

## Ports

- Worker JSON-RPC: **8766** (`ate.worker.server`)
- UI: **5174** (`ate/ui/dev_server.py` via `run_ate_app.bat`)
- Do not use 8765 (AirGPT) or founder-reserved 3000 / 3001 / 5000

## After code the worker loads

Idle-restart with `restart_ate_worker.bat` when you change `ate/core/runner.py`, `ate/worker/**`, `ate/tests/**`, `opa_tests.py`, instrument session helpers. Do not restart mid-run.

Static UI (`ate/ui/web/**`): tell the operator **Ctrl+F5**. Restart the worker if you added/changed an RPC.

`owners.yaml` / `inventory.yaml` / part yaml: RPC re-reads the file. Ctrl+F5 is enough unless the worker is already wedged.

## Checks (run the layer you touched)

```
python -m ate.core.check_new_product
python -m ate.core.check_operator_tree
python -m ate.core.check_ui_contract
python -m ate.core.check_sim_run
python -m ate.core.check_provision_operator
python -m ate.core.check_golden_refs
python -m ate.core.check_stimulus
python -m ate.core.check_walk_order
python -m ate.core.check_family_load
python -m ate.core.check_open_inventory
python -m ate.core.check_test_detect
python -m ate.core.check_ingest_goldens
python -m ate.core.check_golden_gateway
python -m ate.core.check_add_test
python -m ate.core.check_tags_datalog
python -m ate.core.check_lookup
python -m ate.core.check_ingest_datasheet
python -m ate.core.check_cloud_db
python -m ate.core.check_sync_repo
python -m ate.core.check_launch
python -m ate.core.check_visa
python -m ate.core.check_demo_families
python -m ate.core.check_progress
python -m ate.core.check_campaign_outline
python -m ate.core.check_session_values
python -m ate.core.check_specs_datalog
```

A green check that never could fail is not a check. Do not claim PASS without running it.

## Do not

- Add a Tags or Users folder axis under `#Test_Database`
- Hardcode A91 photo cells in Python (use sheet_map)
- Invent a second Excel writer / unpark A13 OneDrive MCP. A14 Recipe canvas is live (closed opcodes only; no eval)
- Scrape en.run-ic.com into `#Test_Database`
- Call `input()` in a `TestSpec.run` (blocks the worker; use Continue / `pause_hook`)
- Import vendor packages (`Lim.*`, `Ariff.*`, `Soo.*`)
- Point stub RUN-IC classes (Power, Comparator, ...) at the OpAmp family
- Use operator=All for Create folders / DEMO / START
- Rewrite the left rail, fonts, or tab chrome "to look modern"
- Touch A16 detect/wrap UI when working A17 tags (and the reverse)
