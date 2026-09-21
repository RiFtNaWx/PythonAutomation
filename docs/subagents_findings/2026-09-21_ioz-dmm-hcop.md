---
keywords: [ioz, dmm, hcop, screenshot, rs1g126, seelim, fill-excel, leftover-honest]
main_idea: IOZ screenshot is DMM (lab_sheet folder IOZ), never MSO. DMM6500 1.7.16a HCOP FORM/DATA is -113; leftover is a :READ? reading-card PNG captured while PSU rails are still on.
---

# IOZ DMM screenshot (not MSO)

## Map (RS1G126 SC70-5, CONFIRMED)

| Pin | Name | IOZ connection | Select |
|-----|------|----------------|--------|
| 1 | OE | PSU CH3 inactive L (active-high buffer) | recipe `oe_active: high` |
| 2 | A | strap GND (don't-care) | not AWG |
| 3 | GND | GND | |
| 4 | Y | PSU CH2 force Vout through DMM DCI | `ioz_vout_list` 0 / 5.5 |
| 5 | VCC | PSU CH1 3.6 V | `ioz_vcc_list` |
| | MSO | not in circuit | Parameters screenshot_from = DMM |
| | Probe | CHA | Setup tick CHB only if recabled |

TestSpec `required_instruments = PSU, DMM`. Stale `_manifest/test_params.yaml screenshot_from: mso` is coerced to DMM.

## What failed

- Live ioz `screenshot_from=mso` wrote a Rigol MSO jpeg of 0 V (MSO unplugged).
- `set_db_context` without `component: Logic` created a junk `OpAmp/rs1g126` tree and wrote dmm yaml there; Logic SeeLim yaml stayed `mso`.
- `:HCOP:SDUM:DATA:FORM PNG` is SYST:ERR **-113** on DMM6500 1.7.16a. User manual screen capture is HOME+ENTER to USB stick, not USBTMC HCOP.
- Runner captured after `_power_down`, so even a working dump would show ~0 A.
- Screenshots used spec.id `ioz/` but sheet_map folder is `IOZ/`.

## Fix

- Skip FORM. Try DATA? briefly. Leftover: reading-card PNG from last IOZ_uA (`_reading_png`).
- Capture inside `_run_ioz` before `_power_down`. Folder = `IOZ`.
- Runner: mso on non-MSO TestSpec -> DMM; skip second dump if TestSpec already shot; SIM DMM dump is allowed (`_SIM_PNG`).
- Fill Excel Path B embeds latest DUT_1 png under the IOZ table.

## Leftover-honest

- Front-panel pixels over USB are leftover on this firmware. Reading card is DMM, not MSO.
- Senior pretty lab book is `never_auto_write`. Fill writes Version `golden_auto` xlsx + csv.
- Junk `OpAmp/rs1g126` tree from the bad context is leftover; do not use it.
