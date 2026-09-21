keywords: aup, delta-idd, yaml-vcc, ioz, screenshot_from, seeLim, rs1g126, leftover-honest
main_idea: AUP DeltaIDD now uses yaml 1.8/2.5/3.3 (Parameters Write still wins). Live SeeLim RS1G126 START ioz with screenshot_from=mso wrote a real MSO jpeg.

PREFLIGHT: HIT. Reuse 2026-09-21_fill-excel-aup-idd-awg.md + 2026-09-21_screenshot-from-mso.md + 2026-09-21_rs1g126-ioz-usb-awg.md.

## Console path (not a new TestSpec)

1. AUP `vih_vil_vcc_list: [1.8, 2.5, 3.3]` already on part yaml. `_delta_vccs` in `ariff_dc.py` honors that list when max < 4.5. Overlay `vcc_list` still wins. G07 stays 0..5.
2. Tests page Parameters -> screenshot_from=MSO -> Write (`save_test_params`) -> START ioz. Same RPC the console uses.

## Proof

- `python -m ate.core.check_add_test` OK
- SIM `delta_supply_current` rs74aup1g07: `DeltaIDD n=3 last=0.400 uA @ 3.3 V`, sweep `[1.8, 2.5, 3.3]`. Overlay `[2.5]` stays one point.
- USB SeeLim RS1G126 SC70-5 Version_1, session open PSU+AWG+DMM+MSO. First START ioz (operator Continue): `IOZ n=2 max_abs=2.838 uA` at 3.6 V, csv written. Second START after Write screenshot_from=mso: `IOZ n=2 max_abs=2.814 uA`, jpeg `ioz/DUT_1/screenshots/ioz_2026-09-21_151107.jpg` (Rigol MSO, CH1 0 V / 100 mV).

## Leftover-honest

- 19 physics_scale pairs still MUST_STAY / draft supply_current.
- Comparator / Interface / Vref / Clock `live: false`.
- IOZ settle NON_TIGHT (not a green tight-settle claim).
- Uncommitted sibling OE-pin / PSU-CH3 ioz tree was not in this worker; live ioz used AWG on the bus.
- Worker still needs idle-restart to load `_delta_vccs` for AUP DEMO on 8766.

## Not proven

- OpAmp RS622 `*_filled.xlsx` after tempfile path (Logic golden_auto fill already ok).
- All-family USB START of every inventory SKU.
