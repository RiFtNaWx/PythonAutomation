keywords: noise, flicker, 0.1-10Hz, en, nV/rtHz, RS622, catalog, inventory yaml, qualification
main_idea: Qualification SKUs already in inventory.yaml; missing part yaml blocked Setup customize. Noise was a 1 ms screenshot stub. Live path is 0.1-10 Hz Vpp / |gain|, not datasheet 11 nV/rtHz.

## Catalog

User paste = Qualification Product List-20260320 Main. `ate/config/inventory.yaml` already 1:1 (lots, PIC, RS0204 level+logic suite). Do not scrape en.run-ic.com.

Part yaml was missing for: rs1gt34, rs1gt08, rs1gt32, rs1g123, rs164, rs1g74, rs74aup1g07, rs358, rs8551. `check_new_product` now fails if any inventory part has no `ate/config/parts/<key>.yaml`.

Customize path stays yaml + TestSpec (PROMPT_GUIDE). No wizard (parked).

## How people test OpAmp noise

1. Spot density en (nV/rtHz) at 1 kHz / 10 kHz: high gain, FFT or analyzer. RS62X RevC.3: 11 nV/rtHz @ 1 kHz, 7.5 @ 10 kHz. Typ only. Not production-tested.
2. 0.1-10 Hz flicker (lab sheet Noise_1_10Hz): high gain, shield, AWG off, AC-couple, ~10 s window, Vpp / |gain|. PDF has no min/max -> VN_IN_PP_uV stays unspec until typed.

## Code

- `ate/tests/opa/noise.py` -- no AUToscale, pause_hook, power_on_protected, no input(), no Excel Pass stamp
- Removed noise from `mapped_dc.CASES`
- `limits/rs622.yaml` EN_* typ-only (not test: noise) + VN_IN_PP_uV
- Worker 0.2.24

Do not invent FFT density on MSO5072 this wave.
