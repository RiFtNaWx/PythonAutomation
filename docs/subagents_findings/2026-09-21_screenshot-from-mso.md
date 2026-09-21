---
keywords: screenshot_from, mso, visa-poison, parameters-write, rs74aup, rs3235, leftover-honest
main_idea: Parameters Write screenshot_from=mso now persists and captures after each test; live MSO JPEG 85 KB after Discover+Open Session. AUP 4/4 and RS3235 6/6 SIM. Fill Excel still timed out.
---

# 2026-09-21 screenshot_from actually captures

PREFLIGHT: HIT. Reuse usb-icc-start-outputs, perfect-ate-goal-wave, pyvisa-load-timing-sim.

## Config path (no new TestSpec)

Cause: Tests Parameters `screenshot_from` was UI-only. `_clean_test_param_block` dropped it, so Write never landed in `_manifest/test_params.yaml`. Live `:DISP:DATA?` also died with VI_ERROR_SYSTEM_ERROR unless the MSO handle was dropped and reopened.

Change (existing runner + save_test_params):

- `database.py` keeps `screenshot_from` as `mso` or `none`
- `RunParams.overlay_for` applies it
- `_run_one` captures after a pass when `screenshot_from=mso` (skip SIM)
- `capture_screenshot` reopens MSO once on poison, then retries

Checks: `check_walk_order` `check_ui_contract` `check_add_test` EXIT 0.

## Proof

1. RS74AUP1G07 SIM 4/4. VIH/VIL `n=3 last VCC=3.3`. IDD still includes 5.5 V (leftover until PDF).
2. RS3235 SIM 6/6 (iq/vinmin/lir/lor/ioutmax/enable_current). Worker all-family 228/236 was empty results after USB leftover, not LDO physics.
3. Discover -> Open Session USB (PSU+DMM+MSO). RPC `screenshot` wrote `live_wave_2026-09-21_145032.jpg` 85005 bytes under Eugene RS622 `MSO/screenshots`.
4. Zip rebuilt: Desktop `ATE_Console_Try_2026-09-21.zip`.

## Leftover-honest

- Fill Excel (`fill_workbook`) timed out 60 s on OneDrive xlsx. Button `#btn-fill-excel` still the path.
- Open Session right after worker restart can return `{}`; Discover then Open Session finds USB.
- AWG still PnP-skip on this bench.
- MUST_STAY 13 + 6 draft supply_current.
- Comparator/Clock `live: false`.
- USB START with Continue + `screenshot_from=mso` Write is the operator click; this turn used Discover+screenshot RPC (same capture_screenshot).
