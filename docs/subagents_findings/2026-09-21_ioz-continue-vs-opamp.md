keywords: ioz, pause_hook, continue, path-b-handoff, vos, screenshot_from, awg-tiles, undefined-header, settle, leftover-honest
main_idea: Pre-fix IOZ was 4 Continues (wire-map + save-paths extra vs VOS). Current path_b_handoff skips IOZ begin dump and all Path B save-paths -- PASS IOZ is fixture + DUT only. Header MSO+AWG green is Open Session map, not TestSpec PSU+DMM. _run_ioz does not send :FREQ. Settle is silent DMM sleep.

PREFLIGHT: HIT. Reuse 2026-09-21_ioz-no-awg, 2026-09-21_awg-undefined-header, 2026-09-21_screenshot-from-mso. No INDEX edit. No code.

# Path B IOZ Continue vs OpAmp VOS

Assume START (not DEMO), `auto_continue=False`, 1 DUT, one test id. Fixture STM `auto_ack` off.

## 1. Popup counts (file:line)

Runner gates (both families):

- Fixture board: `ate/core/runner.py:652-688` (`kind=config_change`, LOGIC vs G201)
- DUT install: `runner.py:810-852` (first DUT always; checklist hardcodes `AWG OFF @ 1 kHz, scope STOP` at `838/840`)
- Channel change: `runner.py:720-765` only if `dual_channel` and a later channel. IOZ `dual_channel=False` (`logic_dc.py:1559,1615-1619`) so CHA-only. VOS omits the flag; registry default `dual_channel=True` (`registry.py:46`) so OpAmp A+B can add a CHB Continue.

Path B IOZ extra (`product_model.py:2500-2526` via `_run_ioz` `logic_dc.py:1489`):

- Wire-map verify: `2508` (`format_handoff_begin` `2441-2453` = wire + stimulus + settle text + measure)
- PASS: save-paths `2522` (`format_save_lines` `2411-2423`)
- FAIL only: attach `2514` (`format_fail_lines` `2426-2438`); no save-paths (`else` skipped)

OpAmp VOS extra (`vos.py:20-24,60-61`): one `_pause(_WIRE)` per channel run. No Path B save/FAIL. Empty checklist -> runner injects AWG/MSO bullets (`runner.py:931-936`).

Count, 1 DUT, PASS:

| START | Fixture | DUT | Channel | Test body | After pass | Total |
|-------|---------|-----|---------|-----------|------------|-------|
| IOZ CHA | 1 LOGIC | 1 | 0 | 1 wire-map | 1 save-paths | **4** |
| VOS CHA-only | 1 G201 | 1 | 0 | 1 `_WIRE` | 0 | **3** |
| VOS CHA+CHB | 1 G201 | 1 | 1 CHB | 2 `_WIRE` | 0 | **5** |
| IOZ FAIL after wire-map | 1 | 1 | 0 | 1 wire-map | 1 FAIL (not save) | **4** |

IOZ looks busier because popup 3 is a long Path B checklist (pin_drive dump still lists AWG at `2321-2326`, then "No AWG" at `2342-2348`) and popup 4 is save-paths after the measurement. VOS is one sentence.

## 2. Why header tiles show MSO+AWG green (TestSpec is PSU+DMM)

`logic_dc.py:1615-1619` `required_instruments=frozenset({"PSU","DMM"})`. Gate is only `_run_one` missing check `runner.py:1157-1158`.

Tiles follow Open Session `instrument_map=self._mapping` (`runner.py:610-611`), not the TestSpec set. USB PnP with DG822+MSO keeps those tiles green (see `2026-09-21_ioz-no-awg.md` live map includes AWG).

Every Continue also `_ask_operator` -> `_safe_idle_for_operator` (`1381-1395`, `1339-1376`): if `instr.gen` is not None, `park_generator_idle` runs even for IOZ. DUT banner still says AWG 1 kHz + scope STOP (`838`). IOZ `park_scope` is False (`942`, TestSpec has no MSO) so MSO is not STOPped on Path B pauses, but the tile was already green from session.

## 3. screenshot_from default vs `:DISP:DATA?`

Default `RunParams.screenshot_from=""` (`runner.py:101`). Overlay sets `mso` only if test_params Write says so (`204-208`). Capture after pass only if `shot in ("mso","scope")` (`1213-1221`), **not** gated on `required_instruments`. Then `capture_screenshot` (`435-460`) -> `capture_jpeg`; poison log names `MSO :DISP:DATA?` (`456`).

Default empty: **no** `:DISP:DATA?` on IOZ. Written `screenshot_from=mso`: **yes**, even though IOZ TestSpec has no MSO (`2026-09-21_screenshot-from-mso.md`).

## 4. Leftover AWG `:FREQ` on current `_run_ioz`?

No in source. `_run_ioz` (`1473-1529`): `_require_for(..., "ioz")` skips AWG (`101-109`); `_ioz_drive_inactive` PSU CH3 only (`619-625`); `_power_vcc` default no AWG (`1496`, `529-542`); never `_apply_levels` / `set_frequency`. Stimulus override `stimulus.py:56-59` and `269-276`: DC, PSU CH1/CH2/CH3, no AWG.

`park_generator_idle` (`generator_setup.py:319-336`) is CH1/CH2 OFF only; `_BANNED_FREQ` (`12`, `24-32`); live `set_frequency` re-APPL (`259-260`). Goldens still have banned headers (`2026-09-21_awg-undefined-header.md`) -- Path C wrap, not this Path B body.

`_power_down` (`546-552`) still `stop_output` if `instr.gen` exists (session leftover, not `:FREQ`). Old worker that still `_apply_levels(pin_drive AWG)` is leftover-honest until idle-restart (`ioz-no-awg.md`).

## 5. Settle as a second "nothing happens"

Not a Continue. `format_settle_lines` (`2359-2377`) is text **inside** the wire-map popup (`2445`). After Continue, `_wait_settled_current_ua` (`481`, `389-468`) `time.sleep(settle_s)` then DMM reads; IOZ calls it 3 times per VCC (`1497-1507`). If `stable_eps_A` null: one sleep then one read (`430-434`). If set: loop until `stable_n` or `settle_timeout_s` FAIL. Banner stays "running"; operator sees a hang, not a new Wait pill.

## Leftover-honest

Parent later skipped IOZ begin dump + all Path B save-paths (`path_b_handoff` `tid != "ioz"`). PASS IOZ is now fixture + DUT only (2 Continues). This file's count of 4 is pre-fix.

Live SeeLim IOZ START may still be the pre-no-AWG worker. This note is source HIT only. Did not START, did not restart, did not edit INDEX.
