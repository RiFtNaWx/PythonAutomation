# VoS research -- handover row 6

**Audience:** Ariff (implementation into board), Eugene, William, OpAmp.  
**Date:** 2026-09-11  
**One sentence:** Software already measures input offset on the **research gain board** (G201 / G1001) and can fill lab VOS cells. The remaining work is a **modular fixture** so the new RS622 board does not need flying leads.

Pictures / sim: keep in the existing "VOS Research" + PCB folders. This file is the software + fixture idea only.

---

## 1. What already exists (do not rebuild)

| Piece | Where | Notes |
|-------|--------|--------|
| Console test | `ate/tests/opa/vos.py` `vos_sweep` | Wraps `opa_tests.test_vos_sweep`. Returns `VOS_mV`. Fixture **G201**. Notes: RESEARCH board only, not the general lab testboard |
| Legacy one-shot | `run_vos_sweep.py` | Discover + 101-point sweep, gain=201. Writes research Excel |
| Research workbook path | `ate/config/bench.yaml` `research_excel` and `ate/core/paths.py` `RESEARCH_EXCEL_PATH` | Default `Downloads\VOS Research.xlsx`. Separate from the campaign lab report |
| Lab report cells | `campaign_outline.py` VOS TTSOP R16:U16 / AA16:AD16; SOP8 B16:E16 / I16:L16 | Filled from living `report.json` like GBW |
| Limits | `ate/config/limits/rs622.yaml` `VOS_mV` | Typical/max from datasheet extract (RS622 max 3 mV in check_lookup) |
| Photos | TTSOP VOS sheet u1_chA A39 ... 8-box | Waveform layout YAML |
| Physics tutorial (legacy wording) | `TEST_DESIGN.md` sections 6-7, `PYVISA_OPA_DEEP_DIVE.md` | Closed-loop / null / DC sweep. "not in repo yet" in TEST_DESIGN is **stale** -- sweep exists |

Operator path today:

1. Setup OpAmp / RS622 / your name / Version. Apply.
2. Fixture mode G201 (or G1001 in outline for vos/vossweep) -- **research board**, not BUFFER/G11.
3. Open Session. Tick **VOS DC Sweep**. START.
4. Lab xlsx VOS sheet gets `VOS_mV` if `paste.values` is mapped. Sweep table may still go to research Excel.

Do not run this on the general characterization board and call it datasheet VOS without Eugene's fixture sign-off.

---

## 2. Physics (what to tell William / OpAmp)

Three methods, same quantity \(V_{OS}\):

| Method | Idea | On this bench |
|--------|------|----------------|
| Closed-loop | Short/ground inputs, \(V_{OS} = V_{OUT} / A_{CL}\) | Fast. Needs known gain and a quiet sense node |
| Null | Step Vin until Vout ~ 0 | Same idea as GBW binary search |
| DC sweep | Step Vin, record Vout, fit intercept | What `test_vos_sweep` does. Best characterization table |

Rules that already bit this repo:

- AWG `offset` is **waveform DC offset**, not opamp \(V_{OS}\).
- Do not `:AUToscale` for absolute DC / Vos.
- High closed-loop gain (G201 or G1001) so DUT offset beats the scope/DMM floor -- same reason Noise uses G=1001.
- `power_on_protected` only. Settle 0.2-1.0 s after each Vin step.

Datasheet RS62X: VOS typical / max in mV. Console stamps pass/fail from `limits/rs622.yaml`, not from "script did not raise".

---

## 3. Idea -- modular section (handover "maybe internally wired")

Goal from the sheet: **implementation into board and test**, modular, **without needing to wire**, or internally wired so VOS can be enabled.

Recommended direction (smallest that works):

1. **Keep one TestSpec** (`vos_sweep`). Do not fork a second console test named "research vos".
2. On the **new RS622 board**, add a VOS module that is a known closed-loop gain (201 or 1001) with:
   - DUT sockets already on IN+/IN-/OUT
   - A jumper / FET / 0 ohm option: **CHAR** (gain network in) vs **APP** (normal GBW/BUFFER path)
   - Sense point for DMM or scope CH to VOUT already routed to the same connector the ATE uses today
3. Fixture mode stays `G201` / `G1001` in `sheet_map` / `ate/fixture/modes.py`. Operator sees one Continue: "Set jumper VOS / install G201 module".
4. When the module is **internally wired**, that Continue becomes a no-op and the recipe can drop the research-board warning.
5. Research Excel (`VOS Research.xlsx`) stays optional for 101-point characterization tables. Daily AE numbers go to the **campaign** VOS sheet (`paste.values`), not a third workbook.

Do not:

- Put flying-lead instructions into `runner.py`.
- Share one research xlsx across operators on SharePoint as the SoT -- that file fights OneDrive. Campaign `workbook/` per person is the SoT.
- Treat Noise 0.1-10 Hz Vpp as VOS.

### Board checklist for Ariff / PCB

- [ ] Gain network 201 and/or 1001, documented in the silkscreen
- [ ] Enable path that does not steal the GBW G11 network
- [ ] Kelvin-ish sense on VOUT if the lead holder allows
- [ ] Guard / ground pour for uV work (same as Noise lid story)
- [ ] Connector pinout matches current G201 research board so `vos.py` does not need new SCPI
- [ ] Picture + PDF in the VOS Research folder (not inside `#Test_Database` code)

### Software leftover after the board exists

- [ ] If jumperless: change `vos.py` notes from "RESEARCH board only" to "RS622 module CHAR".
- [ ] Confirm `VOS_mV` still fills R16/B16.
- [ ] One live START vs datasheet max (check_lookup expects RS622 max 3.0 mV unless limits yaml changes).
- [ ] Optional: stop writing `research_excel` by default so AE does not hunt Downloads.

---

## 4. What to say (about 1 minute)

"VOS is already in the program. Tick the checkbox, it sweeps, numbers go into the lab Excel.

The Downloads file is the long research table. Daily numbers don't go there.

Next job is hardware: put the gain block on the new RS622 board so we stop using flying wires. Same test. No second program.

Ariff does the board. William does the sim. Eugene says when CHAR and GBW won't fight."

---

## 5. Agent prompt (when the board lands)

```
Read docs/handover/VOS_RESEARCH.md and ate/tests/opa/vos.py.
The new RS622 board now has an internal VOS gain module (G201 or G1001). Update TestSpec notes and operator Continue text only. Keep measurement id VOS_mV. Do not call input(). Do not edit runner.py. Do not point research writes at another operator's Version. Run python -m ate.core.check_specs_datalog. Idle-restart worker.
```

References: `TEST_DESIGN.md` tutorials B/C, `PYVISA_OPA_DEEP_DIVE.md`, TI/ADI "op-amp input offset voltage measurement" app notes.
