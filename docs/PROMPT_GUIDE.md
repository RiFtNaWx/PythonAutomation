# Prompt guide (operator console)

Paste one block. Do not invent a second stack. Live product is `ate/` + worker **8766** + UI **5174**.

**Compulsory skills** (auto-use): `.cursor/skills/ate-prompt/` then Path A/B/C in `ate-add-test`, OCR/limits in `ate-ocr`, `ponytail`, `i-have-adhd`. Agent says `Is it like this?` then builds. Same blocks: `.cursor/skills/ate-prompt/prompt-blocks.md`.

How (edit / debug / three add-test paths): [VIBE_CODE.md](VIBE_CODE.md). Where: [AGENTS.md](../AGENTS.md).

**PyVISA / SCPI:** this repo is the golden RAG. Grep `psu_setup.py`, `generator_setup.py`, `dmm_setup.py`, `scope_setup.py`, `ate/tests/**`. Do not paste web SCPI. DG822 Pro `-116 Undefined Header` and "command not in the library" are almost always a copied DG4000/Keysight line.

## Speak -> what we can actually do (paste this)

```
Translate what I said into this repo only. Read docs/PROMPT_GUIDE.md Speak table. Golden SCPI lives in psu_setup.py (DP832 power_on_protected), generator_setup.py (DG822 Pro APPL SQU/DC, OUTP, LOAD INF), dmm_setup.py (DMM6500 :CONF + drain SYST:ERR + 5x :READ? mean, never *RST, never NPLC/AZER/AVER/TRAC/HCOP), scope_setup.py (MSO5072). Call those helpers from ate/tests/<family>/. Never invent a header. Rigol -116 / DMM6500 -113 = delete the write. IDD OVP is 5.6 V not 5.5 (Vset=OVP trips). Do not search online for SCPI.
```

### Operator speak -> code

| They say | Do this | Not this |
|----------|---------|----------|
| Turn PSU on / 3.3 V / 5 V | `power_on_protected(psu, ch, V, I)` in `psu_setup.py` | `power_on`, `:OUTP ON` with no OVP, web DP8xx snippets, 30 V / 3 A |
| Protection / OVP / OC lamp | Keep `PROT:STAT ON`. IDD **OVP=5.6 V** (not 5.5). Default else Vset+0.3, ceiling 6.0 V | 10% of 5.0 = 5.5 at Vset 5.5 (trips). Rewrite STAT every step |
| AWG square 1/5/10 MHz | `setup_square` after `:OUTP1 OFF` (APPL carries freq). No `:SOUR1:FREQ` | `:FUNC:SQU:DCYC`, `:SOUR1:FREQ`, `:OUTP3` (Error 116 on DG822 Pro) |
| AWG DC / CH1 then CH2 | `setup_dc(gen, ch, volts)` + `:OUTP:LOAD INF` | `:APPL:DC` web arity. Keysight `:VOLT:OFFS` |
| DMM current / IDD / CIN | `dmm_setup_current` + `dmm_read_avg` (clear buffer, 5x `:READ?`, mean). Front panel DCI. NPLC/Filter on the box MENU. | `*RST` (**-113**). `:MEAS:CURR?`. `:SENS:CURR:NPLC` / AZER / AVER / `TRAC:CLE` / HCOP |
| DMM voltage / VOH | `dmm_setup_voltage` + 5-read mean | AUTO current range. Web Keysight/Keithley snippets |
| Error -113 on DMM | Same class as Rigol -116. Delete the write. Drain `SYST:ERR?` before every READ so the dialog never sticks. | Google Keithley averaging / TRAC:CLE |
| Error -116 on AWG | Delete OUTP3/4, FUNC:SQU:DCYC, SOUR FREQ. APPL:SQU after OUTP OFF | DG4000 / web Rigol |
| Scope shot / slew | `ate/drivers/mso5072.py` `capture_jpeg` | AUToscale, Tek `:HARDCOPY` |
| Sweep VCC 0 to 5 step 0.5 | Setup **VCC start/stop/step** then START. Delta Supply uses it | Hardcode a second sweep in runner.py |
| Wait 5 s between sweep points | `_SETTLE_S = 5` in `eugene_cap.py` after VCC/freq/AWG change. Log `was`/`d=` | Sleep after the whole test. Web SCPI delays |

## Lessons (this bench -- do not re-learn)

| Hit | Cause | Fix that stayed |
|-----|--------|-----------------|
| DMM Error **-113** | `*RST`, `:SENS:CURR:NPLC` / AZER / AVER / `:TRAC:CLE` / HCOP | `dmm_setup.py` allowlist. Drain `SYST:ERR?`. Host filter = 5x `:READ?` mean after `*CLS`. Never screenshot the error dialog. |
| DMM stays DCV | Only `:SENS:FUNC` without `:CONF:` | `:CONF:CURR:DC` (no extra FUNC/RANG) |
| DCI AUTO hangs | `:RANG:AUTO ON` on current | Fixed `:SENS:CURR:DC:RANG 0.01` |
| AWG Error **-116** | `:OUTP3/4`, `:FUNC:SQU:DCYC`, `:SOUR1:FREQ` | 2-ch `APPL:SQU` after OUTP OFF |
| CIN_pF ~ 0 | C used wanted Hz; AWG did not step | Use APPL Hz; OFF then APPL |
| IDD OVP trip at 5.5 V | Vset = OVP, or 10% of 5.0 | OVP **5.6 V** |
| Random hang after a test | SAFE IDLE `*IDN` MSO + AWG park FREQ | Idle only at Continue; skip MSO on DMM tests |
| Sweeps too fast | yaml `settle_s: 0.3` | `_SETTLE_S = 5` between points |

Synergy: tests never write raw SCPI. Call `dmm_setup_*` / `power_on_protected` / `setup_square` / `setup_dc`. Proof: `python -m ate.core.check_stimulus` and `python -m ate.core.check_all_parts`.

## Operator scenarios (full use)

1. **USB Logic CIN/IDD/CPD** -- Discover, Open Session (KEEP PSU/AWG/DMM), pick Eugene not All, START, Continue on each pause. DMM front panel must show **DCI**. Worker log: `DMM SYST:ERR` only if not 0. 5 s between sweep points. Header STOP if wedged, then `restart_ate_worker.bat` when idle.
2. **DEMO vs START** -- DEMO is SIM (`auto_continue`). START is USB and must wait Continue. Do not treat SIM tiles as live.
3. **OpAmp slew** -- Open USB with MSO. Continue on BUFFER/DUT/channel. PSU OVP is Vset+0.3. AWG APPL SQU 1 kHz. JPEG via `capture_jpeg`.
4. **Add a person / Version** -- Setup Operator folder + Save person. Apply campaign. `#Test_Database/.../{Label}/Version_N`. All is view-only.
5. **Add or wrap a test** -- Tests page: Customize + Save this Version (Path A); Write test / Edit source (Path B); Remember golden (Path C); Copy Cursor prompt. Then `check_add_test` + DEMO that id.

English datasheets: `%USERPROFILE%/Downloads/Reference/Reference` first (`ate/config/datasheets.yaml` index, portable paths). Else `#Test_Database/Reference`. Website https://en.run-ic.com/ only if that SKU has no local PDF. Limits SoT: `ate/config/limits/<part>.yaml`. Truth tables SoT: `ate/config/parts/<part>.yaml`. Ingest recipe: `docs/datasheet/INGEST.md`. Never scrape the RUN-IC catalog into `#Test_Database`. Never store `C:\Users\<name>` in `coverage.json`.

## Vibe-code / debug this repo

```
Live product is ate/ + worker 8766 + UI 5174. Read AGENTS.md then docs/VIBE_CODE.md. Stop at the first Where-to-change row. Do not edit runner.py / database.py path shape unless I name that file. Do not unpark A13/A14. Do not call input() in TestSpec.run. Run the matching check, then DEMO or START once. If it fails: cause + which log (sessions/run_log.txt, report.json, worker window, F12). Idle-restart worker after ate/tests or worker. Ctrl+F5 after UI. Write docs/subagents_findings/YYYY-MM-DD_<topic>.md and update INDEX.md.
```

## Add or change a person

```
Add person <Name>. Write ate/config/owners.yaml via Setup Operator folder + Save person (or Apply campaign). id lowercase ascii, label is the folder. Default this Component/Part/Package as their task. All stays view-only. Do not add a Users folder under #Test_Database. Forget person is yaml only.
```

## Add or change a part we are testing

```
We are testing <RS622> <package> as <OpAmp|Logic|Level|switch|power>. Add/update ate/config/parts/<key>.yaml (enabled_tests, vcc, fixture_modes). Add one inventory.yaml row only because we test it. Create folders with Setup Create folders + open. Do not scrape en.run-ic.com SKUs into #Test_Database.
```

## Customize tests on this Version (Path A -- no new Python)

```
On this campaign only, enable existing TestSpec ids <id,...> via Tests page Save this Version. Write _manifest/test_catalog.yaml enabled_tests. Catalog wins over parts yaml. Do not edit ate/config/parts unless I want every operator of this SKU. Do not invent a TestSpec. Do not copy another person's catalog. Copy-from-part stays parked.
```

## Realize a new test (Path B -- Python)

```
Path B realize test <id> in family <opamp|logic|switch|power> for part <rs1g07>. Create ate/tests/<family>/<id>.py. Import it from that package __init__.py. register(TestSpec) with id, label, required_instruments, fixture_mode, lab_sheet, run, dual_channel=False unless CHA/CHB probe move is required. run() must use power_on_protected and params.pause_hook, never input(), never import Lim.* / Ariff.*. Return measurements [{id, value, unit}] whose id matches ate/config/limits/<part>.yaml specs[].id. Add id to parts/<key>.yaml enabled_tests (shared recipe) and Save this Version if a short catalog would hide it. Idle-restart worker. Map excel_sheet in this campaign sheet_map.yaml if a workbook sheet exists (probe cells, do not guess). Do not edit runner.py. Proof: python -m ate.core.check_add_test then DEMO that id. Worked example: cin/cpd in ate/tests/logic/eugene_cap.py.
```

## Wrap golden then fill (Path C -- scaffold is not done)

```
Path C wrap def test_<name> from <golden file> into family <logic> for this campaign. Tests page Wrap + enable on this Version. That writes imported_<id>.py scaffold plus __init__ import. Block if input() is still in the golden. Then fill run() like Path B (measurements, power_on_protected, pause_hook). Do not call the empty scaffold DEMO a finished test. Do not edit runner.py. Example still-scaffold: imported_input_off_leakage.py. Example filled: eugene_cap.py.
```

## Datasheet min / typ / max then PASS/FAIL

```
For part <RS622>, put electrical limits in ate/config/limits/rs622.yaml specs: id, unit, min, max, typ, test (TestSpec id). English source is en.run-ic.com or a PDF I attach. Do not overwrite filled min/max. After each START/DEMO, sessions/report.json measurements must include min, max, typ, value, result pass|fail|unspec. Export STS datalog.md + datalog.html + datalog.pdf like the STS8200 sheet (Parameter Unit Min Max Typ Value Result). Chip x / fail rows only fail when value is outside min/max. typ is display-only.
```

Operator path without yaml: Results -> **Fetch English datasheet limits** (current SKU only) then **Export STS datalog**. Print HTML to PDF if the simple PDF looks plain.

## OpAmp noise (how people test it)

Do not treat the Noise checkbox as nV/rtHz. RS62X table lists **en = 11 nV/rtHz at 1 kHz** and **7.5 nV/rtHz at 10 kHz**. That is spot density (spectrum analyzer / FFT). The lab workbook sheet is **0.1-10 Hz** flicker:

1. High closed-loop gain (typ G=1001 on the VOS board) so DUT noise beats the scope floor.
2. Inputs quiet (unused pins shorted), linear PSU, shield / lid, AWG **off**.
3. AC-couple VOUT, timebase **1 s/div** (~10 s window), read Vpp.
4. Input-referred uVpp = Vout_pp / |gain|. Stamp `VN_IN_PP_uV`. Datasheet has no 0.1-10 Hz min/max, so result stays `unspec` until you type a limit in `ate/config/limits/<part>.yaml`.

```
For RS622 noise: keep ate/tests/opa/noise.py (0.1-10 Hz Vpp / gain). Do not fake EN_1kHz from that capture. Do not call input(). Do not AUToscale.
```

## After a run that failed

```
Open this campaign sessions/datalog.md and datalog.pdf. List every result=FAIL with value vs min/max. Also read sessions/run_log.txt and report.json measurements. Name the cause (limits miss, missing instrument, catalog hid the test, scaffold wrap, VISA). Do not delete Version folders. Do not stamp the lab xlsx as PASS for DEMO.
```
