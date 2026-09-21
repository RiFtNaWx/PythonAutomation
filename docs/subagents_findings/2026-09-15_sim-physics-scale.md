---
keywords: sim, physics, I=CVf, ICC, IOZ, Schmitt, VAVG, VOLT:OFFS, spec-fail, check_all_parts, leftover-honest
main_idea: USB-unplugged SIM now fail-closes on datasheet specs. Fake PSU/AWG/DMM/MSO follow I=CVf, ICC(VCC), independent CH1/CH2, IOZ Hi-Z, Schmitt Y on PSU CH2, VAVG from DC/OFFS. Nested at_VCC must not inherit ICC_uA max.
---

# SIM physics scale (no USB)

## Proof (2026-09-15)

- `python -m ate.core.check_sim_run` OK (COUNT/VPP off, I=CVf 10x, ICC vs VCC, CH1!=CH2 DC, IOZ Hi-Z, Schmitt Y, VAVG+OFFS, GBW rolloff).
- `python -m ate.core.check_all_parts` OK: **SIM 218/218** parts=26, SPEC judged (not crash-only).
- `python -m ate.core.check_specs_datalog` OK (NaN-with-max fail; at_VCC does not inherit ICC max).
- `python -m ate.core.check_stimulus` OK.

physics_scale on that run: REALIZED=183 LEFTOVER=35. Leftover is honest (1 MHz high-Z iso/xtalk vs 110/550 MHz 50 ohm RF, BUFFER AOL, 0.1-10 Hz noise, Soo wraps). Do not stamp those REALIZED.

## Root causes that made 213/213 a fake green

1. Runner logged SPEC FAIL but left `step.success` True. Fixed: `step.success = ok`.
2. One global AWG bus: DeltaICC CH1 then CH2 overwrote the same func/vpp. Fixed: `_BUS["awg"][1|2]`.
3. `_spec_for` applied `test: icc` max=1.0 uA to nested `at_VCC=5.5`. Fixed: only inherit when meas id is the test id.
4. SeeLim Sub_results used `worst_uA` / `at_VCC`; flatten missed worst_uA. Stamp `ICC_uA` from worst.
5. VOS used `:MEAS:ITEM? VAVG` which returned 0.12; `VOLT:OFFS` ignored. VOS=nan. Fixed: VAVG follows DC/OFFS.
6. SeeLim VIH/VIL sweeps **PSU CH2**, not AWG. AWG-off DMM returned VCC (stuck high). Schmitt Y follows CH2.

## Physics in `ate/instruments/sim.py` (keep)

- PSU OFF -> ~0 A / ~0 V.
- ICC = 50 nA + 0.1 uA/V (stay under 1 uA datasheet max).
- Square I = C(V)*V*f for f >= 100 kHz (3/4/6 pF).
- IOZ: CH2+CH3 ON -> nA Hi-Z, not ICC.
- CMOS VOH~VCC / VOL low from AWG DC vs VCC/2.
- Translator VCCB only if CH2 > VCCA+0.05 and >=1.2 V (not Ariff 80 mV Vref).
- Schmitt: VT+ 0.56*VCC, VT- 0.15*VCC+0.10 (fitted RS1G97 9.2 windows).
- GBW CHAN2 sine 1-pole Av=11; iso/xtalk stay test-body `_SIM_COUPLE`, not G11 CHAN2.

## USB leftover

This sitting is SIM. Live START of every SKU with instruments plugged in is still later.
