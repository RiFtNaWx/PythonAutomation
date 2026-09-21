---
name: ate-add-test
description: >-
  Compulsory format for adding, enabling, wrapping, or realizing an ATE test
  (Path A catalog, Path B TestSpec, Path C snippet pointer). Use when the user
  says add a test, new test, wrap golden, TestSpec, register, cin, cpd, IDD,
  enable tests, Tests page Save, imported_*, measurements, limits specs id,
  snippet pointer, remember + enable, or customize this Version. Do not mix
  paths. Do not edit runner.py.
---

# Add a test (format is the job)

Do not mix Path A / B / C. Full how: `docs/VIBE_CODE.md` section 3. Check: `python -m ate.core.check_add_test`.

Read AGENTS.md first. Pick Path + family + part + TestSpec id before writing Python. Do not ask the operator to paste a Copilot block.

## Pick one path

| Path | When | Writes Python? | Done when |
|------|------|----------------|-----------|
| **A Customize** | TestSpec already exists in this family. This operator Version only | No | Setup shows the id after Tests page **Save this Version** |
| **B Realize** | New physics / new id | Yes: `ate/tests/<family>/<id>.py` | DEMO returns `measurements` `{id,value,unit}` |
| **C Remember + trigger** | Golden `def test_*` exists and has no `input()` / vendor import | No new file. Pointer in `snippet_map.yaml` | START runs the original function |

Family dirs: opamp=`opa`, logic=`logic`, switch=`lim`, level=`level` (suite alias loads logic), power=`power`.

Copy between people / parts is **parked**. Same family only. Do not copy RS0204 dual-rail ids onto RS1G07.

## Path A -- this Version catalog

1. Operator = you (not All). Apply campaign.
2. Setup **Add / edit tests** -> Tests tab.
3. Tick ids that already exist in `load_family(this category)`.
4. **Save this Version** -> `#Test_Database/.../{You}/Version_N/_manifest/test_catalog.yaml`.
5. Catalog **wins** over `ate/config/parts/<key>.yaml`. A short catalog hides `cin`/`cpd`.

Not Path A: a new id missing from the family registry.

## Path B -- realize (this is "add a test")

Worked example: `cin` / `cpd` in `ate/tests/logic/eugene_cap.py`.

Do in order. Skip none.

1. Create `ate/tests/<family>/<id>.py`.
2. Import that module from `ate/tests/<family>/__init__.py`. Forgotten import = missing checkbox.
3. `register(TestSpec)` with `id`, `label`, `required_instruments`, `fixture_mode`, `lab_sheet`, `run`. `dual_channel=False` unless CHA then CHB probe move. `lab_sheet` matches campaign `sheet_map` `excel_sheet` when a sheet exists.
4. `run(instr, params)`:
   - `power_on_protected` (never bare `power_on`, never DP832 30 V / 3 A).
   - `params.pause_hook(title)` (never `input()`).
   - Never `import Lim.*` / `Ariff.*` / `Soo.*`.
   - Return `{"summary": str, "data": dict, "measurements": [{"id": "FOO_uA", "value": n, "unit": "uA"}, ...]}`.
   - Read `params.vcc`, `params.current_limit_a`, `params.unit_index`, `params.part`, `params.vccb`. Do not hardcode leftover RS622.
   - SCPI only from `psu_setup.py` / `generator_setup.py` / `dmm_setup.py` / `scope_setup.py`. IDD OVP **5.6 V**.
5. Shared recipe: add `id` to `ate/config/parts/<key>.yaml` `enabled_tests`.
6. This Version: Path A Save if a short catalog would hide it.
7. Limits: `ate/config/limits/<key>.yaml` `specs[].id` == `measurements[].id`, `specs[].test` == TestSpec `id`. Missing => `unspec`.
8. Excel optional: probe live xlsx into `_manifest/sheet_map.yaml`. Do not guess cells. Do not hardcode A91.
9. Idle-restart `restart_ate_worker.bat`. Ctrl+F5.
10. Proof: `python -m ate.core.check_add_test` then `python -m ate.core.check_family_load` then DEMO **that id**. Open `sessions/report.json`.

Template:

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
    value = 0.0
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

## Path C -- remember + trigger (do not rewrite)

1. Golden `def test_foo` in `logic_tests.py` / `opa_tests.py` / `ate/config/golden_roots.yaml`.
2. Tests page Refresh scan. `input()` / `Lim`/`Ariff`/`Soo` rows stay blocked.
3. Remember + enable on this Version. Stores `file:line` in `snippet_map.yaml` and START triggers that function. Does **not** write `imported_<id>.py`.
4. Change params/limits/thresholds in the original files; next scan stays in sync.
5. Leftover A16: `ate/tests/logic/imported_input_off_leakage.py` may still say `"imported scaffold -- fill body"`. Fill with Path B if you still use it. New wraps must not copy.

## Do not

- Edit `runner.py` to append the test
- Treat Path A Save as a new TestSpec
- Treat Path C scaffold DEMO as realization
- Call `input()` in `TestSpec.run`
- Mix families or copy another operator's catalog
