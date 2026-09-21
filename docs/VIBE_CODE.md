# Vibe-code, debug, and add a test

Live product is `ate/` + worker **8766** + UI **5174**. This page is the **how**. [AGENTS.md](../AGENTS.md) is the **where**. Paste blocks: [PROMPT_GUIDE.md](PROMPT_GUIDE.md). Prompt skill: `.cursor/skills/ate-prompt/` (`Is it like this?` then Path A/B/C). Click path: [DEMO.md](DEMO.md).

Do not grow root `main.py` as a second runtime. Golden `def test_*` files are wrap sources only.

## 1. Every change (same 5 steps)

1. Stop at the first [AGENTS.md](../AGENTS.md) "Where to change" row that matches the ask.
2. Edit only those files. Blast-radius files (`database.py`, `runner.py`, `registry.py`, `worker/server.py`, `ate/ui/web/*`) need a named reason.
3. Run the **matching** check from AGENTS.md Checks. A green check for a layer you did not touch proves nothing.
4. Restart: worker-loaded code (`ate/tests/**`, `ate/core/runner.py`, `ate/worker/**`, instrument helpers) = idle `restart_ate_worker.bat` (not mid-run). UI-only (`ate/ui/web/**`) = **Ctrl+F5**. `owners.yaml` / part yaml / limits yaml = Ctrl+F5 unless the worker is wedged.
5. Click **DEMO (SIM)** or **START** once on `http://127.0.0.1:5174`. A green check is not a demo.

Prefix every Cursor chat with the block in [AGENT_PROMPTS.md](handover/AGENT_PROMPTS.md) section 2 (includes compulsory skills).

## 2. Edit / modify / improve (code, not only yaml)

| I want to... | Files | Proof |
|--------------|-------|-------|
| Change a measurement body | `ate/tests/<family>/<module>.py` `run()` | DEMO that test id; `sessions/report.json` has `measurements` |
| Change which tests this Version shows | Tests page **Save this Version** -> `_manifest/test_catalog.yaml` | Setup checkbox list; do not expect shared `parts/*.yaml` to change |
| Change the shared recipe for a SKU | `ate/config/parts/<key>.yaml` `enabled_tests` | New campaigns pick it up; existing Versions with a catalog keep the catalog |
| Change PASS/FAIL | `ate/config/limits/<key>.yaml` `specs[].id` must equal `measurements[].id` | STS `datalog.pdf` Result column |
| Change Excel number/photo cell | This campaign `_manifest/sheet_map.yaml` (probe the live xlsx) | Results **Fill Excel numbers**; DEMO writes `*_demo.xlsx` |
| Change UI copy / a button | `ate/ui/web/index.html` + `app.js` + `styles.css`, bump `?v=` | `python -m ate.core.check_ui_contract` + Ctrl+F5 |
| Change VISA / SIM | `ate/instruments/` | `python -m ate.core.check_visa` / `check_sim_run` |
| Change START / DUT / channel gates | `ate/core/runner.py` (blast radius) | `check_sim_run` + one DEMO |
| Wrap a golden `test_*` | Tests page **Remember + enable on this Version** | See Path C. Does not rewrite the golden |
| Compile author goldens | `goldens/` + [TUTORIAL.md](../goldens/TUTORIAL.md) + [INDEX.md](../goldens/INDEX.md) | `python -m ate.core.check_ingest_goldens` then `python -m ate.core.check_golden_gateway` |

Legacy `TEST_DESIGN.md` / `opa_tests.py` / `logic_tests.py` are **golden source**. Wrap them into `ate/tests/<family>/`. Editing `main.py` will not show a checkbox on 5174.

## 3. Add a test -- three paths (do not mix)

| Path | When | Writes Python? | Done when |
|------|------|----------------|-----------|
| **A Customize** | The TestSpec already exists in this family. You only want it on **this** operator Version | No | Setup shows the id after **Save this Version** |
| **B Realize** | New physics / new id for the family | Yes: `ate/tests/<family>/<id>.py` (Tests page **Write test** or Cursor) | DEMO returns `measurements` with `id/value/unit`; limits can stamp pass/fail |
| **C Remember + trigger** | Golden `def test_*` exists and does not call `input()` / vendor import | No new Python. Pointer in `snippet_map.yaml` | START runs the original function. Leftover A16 `imported_*.py` is not the happy path |

Copy between people / parts is **parked**. Same family only. Do not copy RS0204 dual-rail ids onto RS1G07.

### Path A -- customize this Version (no Python)

1. Operator = you. **Apply campaign**.
2. Setup **Add / edit tests** -> Tests tab.
3. Under **Customize tests**, tick ids that already exist in this category registry.
4. **Save this Version**. That writes `#Test_Database/.../{You}/Version_N/_manifest/test_catalog.yaml` `enabled_tests`.
5. That catalog **wins** over `ate/config/parts/<key>.yaml`. A short catalog hides `cin`/`cpd` even when part yaml lists them.
6. Default wrap/enable does **not** edit shared part yaml (`update_part_yaml=False`).

Not Path A: a new id that is not in `load_family(this category)`. Ticking a missing id cannot invent a TestSpec.

### Path B -- realize a new TestSpec (this is "add a test")

Worked example already in-tree: `cin` / `cpd` in `ate/tests/logic/eugene_cap.py` + `ate/config/parts/rs1g07.yaml` + `ate/config/limits/rs1g07.yaml` specs `CIN_pF` / `CPD_pF`.

Do these in order. Skip none.

1. **Create** `ate/tests/<family>/<id>.py`. Family dirs: opamp=`opa`, logic=`logic`, switch=`lim`, level=`level` (suite alias loads logic), power=`power`.
2. **Import** that module from `ate/tests/<family>/__init__.py` (`from ate.tests.logic import eugene_cap  # noqa: F401`). Wrap Path C does this for you. A forgotten import = id missing from Setup.
3. **`register(TestSpec(...))`** with all of: `id`, `label`, `required_instruments`, `fixture_mode`, `lab_sheet`, `run`. Set `dual_channel=False` unless the operator must move the probe CHA then CHB. `lab_sheet` must match campaign `sheet_map` `excel_sheet` when a workbook sheet exists.
4. **`run(instr, params)`** must:
   - Use `power_on_protected` (never bare `power_on`, never DP832 30 V / 3 A).
   - Use `params.pause_hook(title)` for Continue (never `input()`).
   - Never `import Lim.*` / `Ariff.*` / `Soo.*`.
   - Return `{"summary": str, "data": dict, "measurements": [{"id": "FOO_uA", "value": n, "unit": "uA"}, ...]}`.
   - Read `params.vcc`, `params.current_limit_a`, `params.unit_index`, `params.part`, `params.vccb` (dual-rail). Do not hardcode a leftover RS622 part.
5. **Shared recipe:** add `id` to `ate/config/parts/<key>.yaml` `enabled_tests` (and `fixture_modes.<MODE>.tests` if that list is the source).
6. **This Version:** Path A Save if you only want it here, or if a short catalog would hide it.
7. **Limits:** `ate/config/limits/<key>.yaml` `specs[].id` == `measurements[].id`, `specs[].test` == TestSpec `id`. Missing limit => `result: unspec`, not fake PASS.
8. **Excel (optional):** campaign `_manifest/sheet_map.yaml` `tests.<key>.excel_sheet` + `paste.values` after probing the live xlsx. Do not guess cells. Do not hardcode A91.
9. **Idle-restart** `restart_ate_worker.bat`. Ctrl+F5.
10. **Proof:** `python -m ate.core.check_add_test` then `python -m ate.core.check_family_load` then DEMO **that id** (DUT 1). Open `sessions/report.json` and confirm `measurements`. Then STS PDF.

Do **not** edit `runner.py` to append the test. Do **not** edit `main.py`.

Template (same shape as `eugene_cap.py`):

```python
from ate.core.registry import TestSpec, register
from ate.core.runner import RunParams

def run(instr, params: RunParams) -> dict:
    hook = params.pause_hook
    if hook is not None and not hook("My slot: wire PSU CH1=VCC, DMM, then Continue"):
        return {"summary": "aborted", "data": {}}
    from psu_setup import power_on_protected
    vcc = float(params.vcc or 3.3)
    ilim = float(params.current_limit_a or 0.10)
    power_on_protected(instr.psu, 1, vcc, ilim)
    value = 0.0  # live: dmm / scope query
    return {
        "summary": f"MY={value}",
        "data": {"VCC": vcc},
        "measurements": [{"id": "MY_uA", "value": value, "unit": "uA"}],
    }

register(TestSpec(
    id="my_slot",
    label="My slot",
    required_instruments=frozenset({"PSU", "DMM"}),
    fixture_mode="LOGIC",
    lab_sheet="MySheet",
    run=run,
    dual_channel=False,
))
```

### Path C -- remember + trigger (do not rewrite the golden)

1. Golden `def test_foo(...)` in `logic_tests.py` / `opa_tests.py` / a path in `ate/config/golden_roots.yaml`.
2. Tests page **Refresh scan**. Scan remembers `file:lineno:fn` in `ate/config/snippet_map.yaml`. Rows with `input()` or `Lim`/`Ariff`/`Soo` stay **blocked**.
3. **Remember + enable on this Version**. START/DEMO of that id calls the original function. No new `imported_<id>.py`. UI never rewrites the source.
4. Change parameters / limits / thresholds in the original files (`ate/tests/`, `parts/*.yaml`, `limits/*.yaml`). Next scan / `list_tests` stays in sync.
5. Leftover A16 copy: `ate/tests/logic/imported_input_off_leakage.py` may still exist with `imported scaffold -- fill body`. Do not treat that DEMO as done. New wraps must not add more copies.

## 4. Check (layer you touched)

| Touched | Run |
|---------|-----|
| New / wrapped TestSpec | `python -m ate.core.check_add_test` then `check_family_load` |
| Detect / wrap / catalog | `python -m ate.core.check_test_detect` |
| DEMO / SIM path | `python -m ate.core.check_sim_run` then `check_demo_families` |
| UI | `python -m ate.core.check_ui_contract` |
| Limits / STS | `python -m ate.core.check_specs_datalog` |
| Excel numbers | `python -m ate.core.check_session_values` then `check_campaign_outline` |
| USB | `python -m ate.core.check_visa` (need `KEEP USB0`, not only `SKIP ASRL`) |

Full list: AGENTS.md Checks. Then still click DEMO or START once.

## 5. Debug (cause -> look here -> fix)

| Symptom | Cause | Fix |
|---------|-------|-----|
| Worker offline / RPC fail | Nothing on 8766 | `run_ate_app.bat` or idle `restart_ate_worker.bat` |
| UI looks old | Cached `app.js?v=` | Ctrl+F5 |
| New test missing on Setup | Module not imported, worker not restarted, or catalog hides it | `__init__.py` import; idle restart; Tests page Save; Apply campaign |
| Wrap DEMO "passes" with empty values | Scaffold not filled | Edit `imported_<id>.py` until `measurements` exist |
| `result: unspec` | Limits id != measurement id | Match `limits` `specs[].id` to `measurements[].id` |
| START disabled | No live/SIM session | Discover -> Open Session, or DEMO / Open SIM |
| DEMO says use Open Session | USB answered `*IDN?` | That is the live path. Do not force SIM |
| Hang / worker dead | `input()` in `run()` | Continue / `pause_hook` only |
| Excel live book unchanged on DEMO | SIM fill uses sidecar | Open `workbook/*_demo.xlsx` |
| Building plan stuck | `get_context` re-import in `run_sequence` | Do not re-import it. Restart idle worker. `check_sim_run` |
| Discover `{}` | Ultra Sigma / no USB | Close other VISA apps, power, Discover again |
| Wrong part (RS622 leftovers) | Campaign not Applied | Apply campaign. `params.part` comes from campaign |
| `venv not found` | Install skipped | `python install.py` from repo root |

Logs: campaign `sessions/run_log.txt`, `sessions/report.json`, `{test}/DUT_n/records/*.json`, worker window, browser F12 Network to `127.0.0.1:8766`.

## 6. Do not

- Edit `runner.py` to add a test
- Call `input()` in `TestSpec.run`
- Treat Path A Save as a new TestSpec
- Treat Path C scaffold DEMO as realization
- Unpark A13 / A14
- Scrape en.run-ic.com into `#Test_Database`
- Copy another operator's catalog into this Version
