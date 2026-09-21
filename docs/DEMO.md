# DEMO -- USB live + SIM backup + extra family acts

Worker **8766**, UI **5174**. Do not use 8765 / 3000 / 3001 / 5000.

Tomorrow (USB + record): Act A. If USB is missing: Act B SIM (same START path, fake SCPI). Extra family acts C-F are SIM-safe rehearsals. Act G is add-test (Path B already in-tree).

Edit / debug / add-test precision: [VIBE_CODE.md](VIBE_CODE.md).

## 1. Install (once per PC)

App user (zip): unzip `ATE_Console_Try_*.zip`, Add shortcut to OneDrive (not Sync), `START.bat`.

Engineer (git): Python 3.11 + Git, `git clone -b eugene-console`, double-click `START.bat` (same file).

Stale UI: **Ctrl+F5**. Worker-loaded code: idle `restart_ate_worker.bat` (not mid-run).

## 2. Campaign (Acts A-B, G)

1. Operator **Eugene** (not All, not Kevin).
2. Left rail **Logic**. Part **RS1G07**, Package **SC70-5** or **SOT23** (Apply must match the tree that exists). Version_1. **Apply campaign**.
3. DUT box: leave **1** ticked. Tick **one** Setup test (not Tests-page boxes). Do not Select-all on USB.

Tree: `#Test_Database/Logic/RS1G07/<Package>/Eugene/Version_1`

## 3. Act A -- USB (record this)

Morning, before the camera:

1. Power + USB: MSO5072, DP832, AWG (DG8xx), DMM6500. Close Ultra Sigma / other VISA apps.
2. `python -m ate.core.check_visa` -- you want `KEEP USB0::...` and `preflight mode=usb`.
3. `run_ate_app.bat`. Browser `http://127.0.0.1:5174`. **Ctrl+F5**.

On camera:

1. **Discover**. Tiles ON. If alert "No USB instruments", stop: cables/power/Ultra Sigma, Discover again.
2. **Open Session** (not DEMO). Hint must say a visa backend, not `SIM session`. PSU output is still OFF until START.
3. Tick **one** test. Photogenic: Logic `supply_current`, or OpAmp rail RS622 **slew**. Eugene `cin`/`cpd` also work; they pause for board + DMM current.
4. **START**. Click **Continue** at each gate (board / DUT). Sleeps are real. PSU will power the socket.
5. Run tab, then Results: Status / Total / Pass / Fail. Open `sessions/datalog.pdf`.
6. **Fill Excel numbers** writes the **live** lab xlsx and can paste photos. Say that before you click it.

Do not START unattended. Do not Select-all. If Open Session fails after a SIM leftover, START disables (session refresh). Retry Discover then Open Session.

**DEMO with USB plugged:** the console refuses DEMO and tells you to Open Session + START. That is the preflight deciding live vs fake.

## 4. Act B -- DEMO (SIM) backup -- Logic RS1G07

No USB, or USB failed *IDN*: **DEMO (SIM)**. Preflight mode=sim, then SIM loopback (PSU/AWG drive, DMM/MSO receive). Fake PyVISA, Continue auto, sleeps skipped. Results still complete. Fill Excel writes `workbook/*_demo.xlsx` (live lab xlsx untouched; no photo paste).

Say: same START path, fake SCPI. Values may be typ / 0 / placeholder. STS PDF still writes.

## 5. Extra SIM acts (more demo, same button)

Each act: Operator Eugene, Apply campaign, DUT 1, tick **one** Setup test, **DEMO (SIM)**. Then Results STS PDF.

| Act | Rail | Part / package | Tick | What to say |
|-----|------|----------------|------|-------------|
| **C** | OpAmp | RS622 TTSOP8 | `slew` | Buffer fixture. AWG + scope. Fixture batch is not Logic DC. |
| **D** | Analog SW | RS2323 MSOP | `iplus` | Switch family (`lim` package). Continue wiring. rON min/max still a datasheet image. |
| **E** | Level | RS0204 TSSOP14 | `vih` | Dual-rail. PSU CH1=VCCA CH2=VCCB. Level rail, logic suite. |
| **F** | Power | RS3213 SOT23-5 | `iq` | Stub-capable. Do not claim a full LDO suite. |

Proof without clicking: `python -m ate.core.check_demo_families` (cin+cpd, iplus, vih, iq, slew).

Do not Select-all. Do not use operator All.

## 6. Act G -- add-test rehearsal (already realized)

Do **not** invent a throwaway TestSpec on camera. Show Path B that already exists:

1. Cursor: `ate/tests/logic/eugene_cap.py` `register(TestSpec(id="cin"` and `measurements` `CIN_pF`.
2. `ate/tests/logic/__init__.py` imports `eugene_cap`.
3. `ate/config/parts/rs1g07.yaml` `enabled_tests` includes `cin` / `cpd`.
4. `ate/config/limits/rs1g07.yaml` specs `CIN_pF` / `CPD_pF`.
5. Console: Logic RS1G07, Apply, tick **cin**, DEMO (SIM). Results show CIN_pF.

Then contrast Path A vs Path C (do not mix):

- Path A: Tests page **Save this Version** writes `_manifest/test_catalog.yaml` only. Hiding `cin` here hides it even if part yaml lists it.
- Path C: Wrap writes `imported_<id>.py` with `"imported scaffold -- fill body"`. Open `ate/tests/logic/imported_input_off_leakage.py` -- that DEMO is **not** a measurement.

Precise steps: [VIBE_CODE.md](VIBE_CODE.md). Check: `python -m ate.core.check_add_test`.

## 7. What to say about reports

| File | Line |
|------|------|
| `sessions/datalog.pdf` | STS: Parameter / Min / Max / Typ / Value / Result |
| `report.json` | Living latest (merge, does not wipe unrun tests) |
| `{test}/DUT_1/records/*.json` | Per-test history |
| USB Fill Excel | Live campaign xlsx |
| SIM Fill Excel | `*_demo.xlsx` sidecar |

## 8. Edit / improve (do not rewrite the runner)

New physics = Path B (file + `__init__` + yaml + limits + restart). Customize this Version = Path A. Wrap golden = Path C then fill. Do not edit `runner.py` / `database.py` path shape / `main.py`.

Person = `owners.yaml` folder. Family = left rail. Same part, different people = two operator folders.

Debug: `sessions/run_log.txt`, worker window, browser F12. Table in VIBE_CODE.md section 5.

## 9. Proof

```
python -m ate.core.check_visa
python -m ate.core.check_sim_run
python -m ate.core.check_demo_families
python -m ate.core.check_add_test
python -m ate.core.check_ui_contract
python -m ate.core.check_family_load
```

`check_visa` green with only `SKIP ASRL` does **not** prove USB gear is plugged in. Act A needs `KEEP USB0` (or USB1) after you connect.
