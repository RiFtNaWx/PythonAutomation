# ATE plug-in checklist (one-prompt scale)

Companion to `ATE_MODULAR.md`. **Vibe-coders / agents: start at repo-root `AGENTS.md`**
(where to change files, add a person, add a version, blast radius). Copy-paste
prompts: `docs/PROMPT_GUIDE.md`. This page is the slot list when you are
already adding a family or campaign.

Fill **every** slot below when adding a family or a new campaign. Do not invent
instruments. Do not clone GitHub into the test tree (`Github_Auto/` is a team
git helper, not ingest).

## Code slots

1. **Family package** — `ate/tests/<family>/` with `__init__.py` that imports
   modules which call `register(TestSpec(...))`.
   - OpAmp example: `ate/tests/opa/` (`vos`, `ac_*`, `slew`, `gbw`, `ort`, …).
   - Logic / Level already have package keys; Level is still a stub suite.
2. **`register(TestSpec)`** — each test: `id`, `label`, `required_instruments`,
   `fixture_mode`, `lab_sheet`, `run` callable. Optional: `notes`, `fixed_steps`,
   `dual_channel`, `short_tag`.
3. **Family map** — built-ins stay in `FAMILY_PACKAGES` (`ate/core/registry.py`):
   opamp → `ate.tests.opa`, logic, level. **New families do not need a hand
   edit.** Prefer `ate/config/extra_families.yaml` (`families.<key>.package`)
   and/or a package under `ate/tests/<family>/` (pkgutil discovery). Worker
   `set_family` / UI rail read `known_families()`.
4. **Optional part yaml** — `ate/config/parts/<key>.yaml` (fixture modes, gain
   boards, sample_size). Electrical min/typ/max live in
   `ate/config/limits/<key>.yaml`. Return measurements from `run()`. Only if
   the part needs bench defaults.
5. **Worker restart** — ingest calls `refresh_family_table()` in-process. If
   the family rail is stale, `restart_ate_app.bat` (ports **8766** worker,
   **5174** UI). **8765 is AirGPT — leave it alone.**
6. **Instruments** — Discover classifies MSO / PSU / AWG / **DMM** (`ate/instruments/discovery.py`).
   DMM is optional at Open Session. Tests that need it (Logic IDD/VOUT/cap_load, OpAmp VOL)
   fail at run if it is missing. Header tile **DMM** turns on when found.

## GitHub / local family ingest

Setup → **Import family** (RPC `import_family`). This is the next-time drop-in
path. It is **not** a clone of this repo and it does **not** `git init` under
`ate/`.

1. Paste a GitHub URL (`https://github.com/org/repo`, `org/repo`, or
   `.../tree/<branch>/path/to/family`) **or** a local family folder / `.py`.
2. Optional family key (example `analog`). Do **not** use `opamp` / `opa` /
   `logic` / `level` — those packages are protected. Do not ingest into opamp.
3. Worker downloads a zipball (or copies the local folder) into a temp dir,
   then copies **only** `*.py` test modules into `ate/tests/<family>/`.
4. Fail-closed: the source must look like an ATE family (`register(TestSpec)`
   or a thin adapter that still calls `register`). A random repo, or this
   full ATE tree (`ate/core` + `ate/tests/opa`), is rejected with the slot
   list above.
5. Existing `opamp`/`logic`/`level` modules are never the dest. Replacing a
   previous extra family backs it up under `ate/tests/_backup/`.
6. `ate/config/extra_families.yaml` is updated. No secrets. Then the worker
   reloads the family table; extra keys appear on the Family rail.
7. Then: Apply campaign → Discover → Open Session → select tests → START.
   Workbook paste cells still come from `import_workbook` + `sheet_map`, not
   from this ingest.

## Campaign slots (`#Test_Database`)

Tree: `{Component}/{Part}/{Package}/{Operator}/{Version_N}/`

Operator is a person folder (Eugene / Ariff / …). Top-right **All** is view-only -- Create folders / DEMO / START require a real person. Migrate legacy trees with `python -m ate.core.migrate_operator_folders --apply`.

6. **Campaign folders** — `_manifest/`, `workbook/`, `sessions/`, plus per-test
   `{TestKey}/DUT_N/{screenshots,graphs}`.
7. **Workbook xlsx** — live lab report under `workbook/`. Import an existing
   file from Setup (RPC `import_workbook`); do **not** use an upload wizard.
8. **`_manifest/sheet_map.yaml`** — folder ↔ Excel sheet ↔ paste anchors.
   Same outline keys as RS622 TTSOP8 (`fixture_mode`, `automated`,
   `dut_iterations`, `naming`). Known numeric cells come from
   `ate/core/campaign_outline.py`. Import upgrades in place; it does **not**
   write FILL_ME. Omit `paste.photos` until measured.
9. **`_manifest/test_catalog.yaml`** — operator conditions / recipes (not
   invented by import).

Excel writes go through `ate/reporting/lab_report.py` + `sheet_map` only.

## PSU safety (A15)

Always use `power_on_protected`. Defaults OVP=Vset+0.3 V, OCP=Iset+0.1 A; PROT:STAT ON with readback. Never DP832 30 V / 3 A. Unprotected `power_on` raises.

## Photo / waveform layout (A07)

**Where to change image boxes:** campaign `_manifest/sheet_map.yaml` → `tests.<TestKey>.paste.photos`
(example `u1_chA: A91`, ORT `pos_u1_chA: A46`). Python paste reads
`ate/reporting/photo_layout.py` only -- do not add another A91 dict in `lab_report.py`.

Preview + compare + save: operator console **Results → Waveform layout** (`http://127.0.0.1:5174`).
Save patches the same YAML. Graphs/screenshots stay under `{TestKey}/DUT_N/{graphs,screenshots}`.

## Mapped tests + DMM (A08)

Every `_manifest/sheet_map.yaml` `tests.<key>.excel_sheet` must have a `TestSpec.lab_sheet`.
Setup shows **Map coverage OK**. Remaining OpAmp sheets (PowerOn / EMIRR / PSRR / CMRR / AOL / VOL / Noise)
run as capture + optional DMM read in `ate/tests/opa/mapped_dc.py` -- not RuntimeError stubs.
Check: `python -m ate.core.check_mapped_tests`.

## Family conditions + timing (A04)

Each family owns its Run param catalog and measurement timing defaults.
`ate/core/param_defaults.py` exposes `catalog_for_ui(part, family=...)` and
`timing_for(family, test_id=...)`. OpAmp keeps G11 gain profiles, GBW steps,
and OPA `TEST_DEFAULTS`. Logic gets Logic-relevant fields (e.g. `vcc`) with
no G11 / `cfg_g11` chrome. Other families (`demo_ingest`, ingested extras)
get a family-local catalog only -- do **not** copy OPA settle/timeout literals
(`1.5` / `1.8` / `6.0` s) as the platform default for non-opamp families.
Worker `list_param_defaults` and the UI reload the catalog on family switch.

## Logic campaigns (A09)

Ariff / Soo / Lim are **owner recipe trees** in LabAutomation-1, not three consoles.
One Logic family rail; differences live in YAML:

1. Campaign: `#Test_Database/Logic/<Part>/<Package>/Version_N/` with
   `_manifest/sheet_map.yaml` + `test_catalog.yaml` (+ workbook via Import xlsx).
2. Part yaml: `ate/config/parts/rs29511.yaml` (Soo) and `rs1g08.yaml` (Ariff) --
   fixture `LOGIC`, `vcc`, `current_limit`, timing (`htol_ns`), `enabled_tests`.
3. Run list filters by `enabled_tests` / catalog so RS29511 does not show
   RS1G08-only DC rows. Extra Ariff specs live in `ate/tests/logic/ariff_dc.py`
   (no `import Ariff.*`).
4. Map coverage / lab-report sync follow the **active** campaign family
   (Logic vs OpAmp). Check: `python -m ate.core.check_logic_campaign`.
5. RS1G07 / RS1G14 use the same Logic family + Ariff DC ids via part YAML (A10).
6. RS0204 dual-rail: `ate/config/parts/rs0204.yaml` (vcca/vccb) + campaign `Logic/RS0204/TSSOP14`. Bodies in `ate/tests/logic/rs0204.py` (PSU CH1=VCCA, CH2=VCCB). Do not import `Soo.logic_tests`. Downloads `logic_tests.py` is RS29511/Soo. Check: `python -m ate.core.check_logic_campaign`.
7. Campaign Component folder switches Family (OpAmp/Logic/AnalogSwitch/Level). `set_db_context` calls `family_for_component`.
8. A12 Ariff latest: thickened DC + `supply_current_sweep` / `vih_vil` / `voh_load` / `vol_load`
   (ids distinct from RS0204 `voh`/`vol`). Tables in part YAML. Operator deselects via checkboxes.
   LDO not on RS1G. Reference: Ariff Repo `LabAutomation_v1 - Copy` (do not import).

## Analog Switch (was mislabeled Lim)

1. Builtin family key `switch` -> `ate/tests/lim/` (package name historical). Alias `lim` still loads it.
2. Part `ate/config/parts/rs2323.yaml` + campaign `#Test_Database/AnalogSwitch/RS2323/...`.
3. Operator (person) is the top-right selector, not a family. Lim also owns Logic RS1G126/RS1G97.
4. Tests: iplus, leakage_off, leakage_on, input_leakage -- PSU+DMM; wiring via
   operator Continue (`pause_hook`), **never** `input()` and **never** `import Lim.*`.
5. Fixture mode `LIM_RS2323`. Check: `python -m ate.core.check_open_inventory`.
6. LA-1 `Lim/threshold_tests.py` is RS1G126 -- Logic, not Analog Switch.

## How to extend (names, tests, corners)

Do **not** edit `runner.py` to add a product. Full no-code wizard stays parked.
Precise Path A/B/C + debug: `docs/VIBE_CODE.md`. Check: `python -m ate.core.check_add_test`.

1. **New person / operator** -- Setup Save person, or a row in `ate/config/owners.yaml`.
2. **New part in an existing family** -- `ate/config/parts/<key>.yaml` then Create folders / Apply.
3. **Path B realize a new test** -- `register(TestSpec)` in `ate/tests/<family>/` + `__init__.py` import + `measurements` + part `enabled_tests` + limits `specs[].id` match. Idle-restart worker. Do not edit `runner.py`.
4. **Path A customize this Version** -- Tests page **Save this Version** writes `_manifest/test_catalog.yaml`. Catalog wins over part yaml. Does not invent a TestSpec.
5. **Path C remember + trigger** -- Tests page Remember + enable stores `file:line` in `snippet_map.yaml` and START calls that function. No new `imported_<id>.py`. Rows with `input()` or `Lim`/`Ariff`/`Soo` stay blocked. Vendor goldens stay Path B. Check: `python -m ate.core.check_test_detect`.
6. **Copy tests between people/parts** -- parked. Same family only if ever unparked. Never RS0204 ids onto RS1G07.
7. **Dropdown corners** -- part yaml `vcc_sweep_list` / `vccb` -> Setup Run conditions.
8. **New family** -- Setup Import family, or `ate/tests/<family>/` + `extra_families.yaml`.
9. **Campaign tree** -- `{Component}` folder switches family.
10. **Tags + STS** -- see `AGENTS.md`. Checks: `check_tags_datalog`, `check_ui_contract`.

Authoring contract for Path B bodies:

```python
def run(instr, params: RunParams) -> dict:
    # power_on_protected; params.pause_hook for Continue; never input()
    return {"summary": "...", "data": {}, "measurements": [{"id": "FOO_uA", "value": 0.8, "unit": "uA"}]}
```

Raw `def test_foo(instr, ...):` is golden-source only until wrapped (Path C) and filled (Path B).

## New product + DEMO (tracking sheet, not website catalog)

1. Setup **New product under test**: pick RUN-IC class (`ate/config/run_ic.yaml`) or a tracking-sheet row (`ate/config/inventory.yaml`), enter part/package, **Create folders + open**.
2. Creates `#Test_Database/{Component}/{Part}/{Package}/{Operator}/Version_1/` with `_manifest/`, `workbook/`, `sessions/`, `Setup/DUT_N/{screenshots,graphs}`. Stub part yaml only if missing.
3. Do **not** add RUN-IC homepage SKUs (RS724-Q1 / RS722P-Q1 / ...) until that part is actually under test.
4. **DEMO dry-run** walks selected tests with mock MSO/PSU/AWG/DMM numbers. Writes `sessions/session_*.json` and `DUT_1/graphs/demo_sample.json`. Does not stamp the lab xlsx PASS.
5. Advanced bench (freq / amp / repeats) sits under DUT/Channel. Photo cells stay Results -> Waveform layout.

Then: Apply campaign -> Discover -> Open Session -> select tests -> START.

## After plug-in

- Apply campaign in Setup → Discover → Open Session → select tests → START.
- Confirm family rail shows the new family and `list_tests` returns the specs.
