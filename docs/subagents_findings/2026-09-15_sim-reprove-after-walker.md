keywords: sim, reprove, walker, y_invert, rs1g14, pause_hook, mapping-empty, leftover-13, leftover-honest, goal-open, check_live_usb
main_idea: Re-ran SIM after invert + walker. 218/218 REALIZED=205 LEFTOVER=13. Closed walker mapping-empty-as-done and USB auto_continue skip. RS1G14 VOH still A=0. Goal OPEN.

# SIM reprove after walker (2026-09-15)

PREFLIGHT: HIT. Reuse `2026-09-15_inverter-y-polarity.md` and `2026-09-15_live-usb-walk-ignore-dmm.md`. Last SIM 218/218 was not re-run during the live walk. This pass inspected current tree then re-ran checks. Did not UpdateGoal complete. Did not Discover / Open Session / live START. No PyVISA. No NI-VISA. No runner.py.

## Verdict

SIM n/ok: **218/218**. REALIZED=205 LEFTOVER=13.
Regressions fixed: walker mapping-empty START + auto_continue skip.
rs1g14 VOH: not buffer polarity (A=0, Y~VCC).
imported_input_off_leakage: still scaffold, not enabled.
Goal: **OPEN**.

Checks this pass:

- `python -m ate.core.check_add_test` OK
- `python -m ate.core.check_sim_run` OK (`inverter_a_high_y_not_vcc` Y=0.001; `inverter_a_low_y_vcc` Y=5; RS1G14 VOH A=0 Y~VCC)
- `python -m ate.core.check_all_parts` OK `SIM 218/218 physics REALIZED=205 LEFTOVER=13`
- `python -m ate.core.check_live_usb selfcheck` OK `rpc=run_sequence_async`

Did not idle-restart worker (only `check_live_usb.py`; not worker-loaded). Did not run `resume`.

## Current tree (authority)

- `ate/instruments/sim.py:47` / `:76` `y_invert` default False; `:80` `set_y_invert`; `:371-381` invert only when flag set; `:684-691` loopback
- `ate/tests/logic/ariff_dc.py:81-97` yaml flag + clear in `_power_down`; `:763` VOH `a_voh = 0.0 if invert else vcc`; `:837` VOL `a_vol = vcc if invert else 0.0`; `:667-683` VIH/VIL edge flip
- `ate/config/parts/rs1g14.yaml:16` `y_invert: true`
- `ate/core/_check_data/sim_stamps.json` n=218 ok=218 ran=218 (rewritten this pass)
- `ate/core/_check_data/physics_enabled.json` n=218 realized=205 leftover=13; every leftover row has a `file`

rs1g14 stamps after this SIM: VOH_1p65V=1.65 ... VOH_5p0V=5.0 VOH_5p5V=5.5 (A=0); VOL_*=0.001 (A=VCC).

## Closable holes found+fixed (walker, not leftover 13)

1. Mapping-empty START -- `check_live_usb.py:446-447` abort walk when `not live`. No `open_session` / `run_sequence_async` while mapping `{}`.
2. Mapping-empty FAIL treated as done -- `RETRYABLE` now includes `open session first` / `mapping is not live usb` (`check_live_usb.py:218-239`). Empty error stays retryable. `_keep_row` selfcheck fails closed.
3. pause_hook USB skip/hang -- START was `auto_continue: True` (DEMO skip after `_ask_operator` safe-idle). Now `auto_continue: False` (`check_live_usb.py:489`). Continue via `get_pending_prompt` + `operator_respond`. Continue RPC fail raises `worker rpc lost` (`:300-304`), not silent 1200s wait.

Did not Discover. Did not Open Session. Did not live START.

## Not a hole this pass

- RS1G14 VOH buffer polarity -- already Path B A=0 + SIM invert. Re-proved.
- `imported_input_off_leakage.py:31` still `imported scaffold -- fill body`. Not in any `parts/*.yaml` `enabled_tests`. `check_all_parts.py:512-515` fail-closes if filled/enabled.

## Leftover 13 (must stay; do not reclassify)

`MUST_STAY_LEFTOVER` is `physics_scale.py:112-126` / `:149-150`.

1. lm358 settling -- `ate/tests/opa/settling.py:73` CHAN2 VPP; `:128-137` SETTLE_VPP_V. Not 0.1% SETTLE_us.
2. rs358 settling -- same body.
3. rs622 settling -- same body.
4. rs0302 i2c_ron -- `ate/tests/logic/rs0302.py:119` / `:127` 10 mA. Datasheet 64 mA leftover.
5. rs2227 usb_ron -- `ate/tests/lim/rs2227.py:5` PDF image rON; `:44` / `:109-111` 10 mA force.
6. rs2227 usb_iso -- `ate/tests/lim/rs2227.py:186-208` 1 MHz high-Z. Not 550 MHz 50 ohm.
7. rs2227 usb_xtalk -- same helper / same BW leftover.
8. rs2323 ron -- `ate/tests/lim/rs2323.py:409-414` / `:421` 10 mA; PDF rON leftover.
9. rs2323 iso -- `ate/tests/lim/iso.py:1-5` / `:21-29`. 1 MHz high-Z, not 110 MHz RF.
10. rs2323 xtalk -- `ate/tests/lim/xtalk.py:1-5` same 1 MHz / 70 MHz leftover.
11. rs358 noise -- `ate/tests/opa/noise.py:1-4` 0.1-10 Hz Vpp, not nV/rtHz.
12. rs622 noise -- same body.
13. rs8551 noise -- same body.

## Named leftover-honest (not leftover 13)

- GBW runner `_pause` auto-returns (`runner.py:846-850`). Do not edit runner.py.
- LIR/LOR VIN-as-VOUT -- `ldo.py` / `_dmm_volt` follows VIN.
- SR~5.55, GBW 7.006, DELAY two-bin, pulse 0.5/f, TR/TF 5 ns MSO 70 MHz, VOS_mV=0, OVERSHOOT=0 -- same as prior audits.
- live USB mapping still `{}` -- human Discover then `python -m ate.core.check_live_usb resume`.
- `imported_input_off_leakage.py:31` scaffold. Not enabled.

## Do not

- Reclassify leftover 13 as REALIZED.
- Fill or enable `imported_input_off_leakage`.
- Globally invert `_dmm_volt`.
- Edit `runner.py` / goldens rewrite / `input()` / `Lim` / `Ariff` / `Soo`.
- Close goal (live USB DMM on RS1G14 Y unproven; leftover 13 is method ceiling).
