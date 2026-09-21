---
keywords: goal, perfect-ate, dmm-mso-y, loopback, pack-zip, logic-app-scale, leftover-honest
main_idea: DMM and MSO now share one DUT Y on SIM (loopback 34/34). Logic worker DEMO 202/202. Zip packed. 19 leftover-honest rows remain. Not USB START / not Verify PASS.
---

# 2026-09-21 Perfect ATE goal -- first wave

PREFLIGHT: HIT. Reuse physics-scale-demo, logic-app-scale-demo, cloud-db-no-block-pick.

## Objective (not complete)

Ship a perfect operator ATE: every SKU, DMM/MSO same Y, scale loop, waveforms, zip download, live USB usecase.

## Proven this turn

1. Logic worker DEMO/SIM **202/202** parts=24 `preflight=sim`. Not USB START.
2. `loopback_check` **34/34** including `dmm_mso_y_agree_*` and `dmm_mso_chan2_y_agree_vin_1p20`.
3. `check_sim_run` EXIT 0. `check_add_test` EXIT 0. `physics_scale` 264 rows REALIZED=245 LEFTOVER=19.
4. Zip: `Desktop\ATE_Console_Try_2026-09-21.zip` (2.8 MB, 290 files, START.bat at top).
5. All-families worker SIM: opamp/logic/level/switch/power ran; RS74AUP1G07 vih_vil now `n=3 last VCC=3.3` (was inventing 4.5..5.5).
6. Bench USB keep: PSU DP8C281601446, AWG DG8Q281600755, DMM 04676344, MSO MS5A281500878. `visa_known.yaml` updated.

## Fix (DMM vs MSO)

Cause: SIM DMM CH2 used Schmitt hysteresis always; MSO VAVG used CMOS `0.4*VCC`. VIN=VCC also tripped OpAmp dual-rail skip on MSO only (`DMM=3.3 MSO=0.001`).

Change:

- Shared `_dmm_volt()` for MSO VAVG CHAN1 (AWG off, CH2 on) and CHAN2 (AWG DC Y).
- `set_schmitt` on the bus. Path B `logic_dc` / `ariff_dc` set it from `product_model.schmitt`.
- Default CMOS so GT 1.20/1.45 still matches MSO live.
- `Instruments` prints missing PSU/AWG/DMM/MSO (was dead code after `awg` return). Alias `.mso`.

Not: `runner.py` / `database.py`.

## Still open

- Live USB START of a wired DUT (PSU/AWG/DMM/MSO all PnP OK on this bench). SIM is not Verify PASS.
- MUST_STAY_LEFTOVER 13 (iso/xtalk/ron/settling/noise) + 6 draft `supply_current`.
- RS74AUP1G07 IDD still sweeps 5.5 V (vih_vil now 1.8/2.5/3.3 only). Wait sample / PDF.
- Comparator / Interface / Vref / Clock `live: false`.
- Wave record on live MSO: Open Session (not SIM) then `screenshot_from=mso`.

## Commands

```
venv\Scripts\python.exe _tmp_loopback.py
venv\Scripts\python.exe -m ate.core.check_sim_run
venv\Scripts\python.exe -m ate.core.check_add_test
venv\Scripts\python.exe pack_ate_console.py
venv\Scripts\python.exe _tmp_all_families_app_scale.py
```
