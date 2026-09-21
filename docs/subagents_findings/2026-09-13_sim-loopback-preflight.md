---
keywords: sim, loopback, psu-off, bench-preflight, usb, signal, received, demo, visa-inventory
main_idea: Do not assume PSU/AWG are ON. Preflight lists KEEP/SKIP *IDN (mode usb vs sim). SIM bus couples drive to receive; loopback must pass before DEMO/Open SIM.
---

# 2026-09-13 SIM loopback + bench preflight

## Was wrong

DMM `:READ?` voltage was hardcoded `3.300` and ICC ~0.8 uA with PSU OFF. Scope COUNT was 120 with AWG OFF. DEMO always opened SIM even if USB answered *IDN.

## Now

- `_BUS.psu_on` / `psu_v` follow `power_on_protected`. DMM volt/current floor when PSU OFF.
- AWG OUT OFF -> VPP floor, COUNT 0. OUT ON -> VPP follows APPL, COUNT 120.
- `loopback_check()`: off -> on -> AWG received -> off. `open_session(sim=True)` refuses if it fails.
- `visa_inventory` / `bench_preflight`: *IDN on KEEP only. `powered_output` is always false (START turns PSU ON).
- DEMO: `mode=usb` -> abort (use Open Session + START). `mode=sim` -> loopback then run.

## Does not prove

- Live USB START / Continue on hardware (tonight KEEP none).
- That a USB-enumerated box has CH1 output ON.
