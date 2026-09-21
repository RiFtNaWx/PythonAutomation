---
keywords: sim, npr, overshoot, g11, buffer, sssr, leftover-honest, rs1g14
main_idea: BUFFER NPR CHAN2 no longer stamps G11*6 V (66 V). OVERSHOOT is 0 (1-pole), not the 0.12 unknown-item dummy. RS1G14 VOH/VIH stays leftover-honest -- no DMM invert. Leftover 13 unchanged. Goal OPEN.
---

PREFLIGHT: PARTIAL
reuse: `docs/subagents_findings/2026-09-15_sim-serial-q7-pwid.md`, `2026-09-15_sim-stamp-must-ids.md`
spawn: skip

# SIM BUFFER NPR + OVERSHOOT dummy (2026-09-15)

## Closed this sitting

1. `ate/instruments/sim.py`: CHAN2 volts-class SIN (vpp>0.2) is BUFFER Av=1 clipped to rails. Was G11 1-pole * 6 Vpp = 66 V on NPR. G11 GBW ~50 mVpp unchanged.
2. MSO OVERSHOOT is modeled as 0 (SIM 1-pole, no ring). Same `:MEASure:ITEM? OVERshoot,CHAN2` USB path. Was fallback 0.12 dummy.
3. Fail-closed: NPR_VPP_V>15 fails. OVERSHOOT==0.12 fails. loopback `npr_chan2_not_g11` / `overshoot_not_dummy`. check_add_test bans DMM invert.

## Not closed (leftover-honest, not leftover 13)

RS1G14 VOH/VIH/VOL Path B still drives buffer polarity (A=VCC for VOH). USB inverter needs A=0 for VOH. Do not invent CMOS invert on the DMM rail. Body stimulus vs USB is still wrong; closing it without a DUT model would SPEC FAIL SIM VOH mins.

## Proof

```
python -m ate.core.check_add_test
python -m ate.core.check_sim_run
python -m ate.core.check_all_parts
```

SIM **218/218**. physics REALIZED=205 LEFTOVER=13. `sim_stamps.json` n=218 ok=218.

File stamps: lm358/rs622 NPR_VPP_V=5.5 (was 66). SSSR OVERSHOOT=0.0 (was 0.12). G11 GBW Av still ~11 at 50 mVpp.

## Leftover-honest (not leftover 13)

- SIM LIR_mV ~1600: no LDO model.
- LM358 SR_Vus ~5.55 vs typ 0.5: SIM 1-pole slew.
- all-GBW GBW_MHz=7.006 SIM G11 1-pole.
- rs0204 tsu/th TEN_ns/TDIS_ns; FMAX 20 vs PDF 50; TR 5 ns vs typ 6.6.
- SIM DELAY two bins ~50 ns.
- SIM pulse_width 0.5/f, not board RC.
- RS1G14 DC polarity SIM-buffer. USB invert needs opposite AWG DC.
- NPR clip is rail-sum leftover, not a phase-reversal SPICE model.
- SSSR OVERSHOOT=0 leftover 1-pole, not a measured ring.

## Leftover 13 (must stay; do not reclassify)

iso/xtalk 1 MHz not 110 MHz; usb_iso/usb_xtalk 1 MHz not 550 MHz; ron/usb_ron/i2c_ron 10 mA; settling SETTLE_VPP_V not 0.1% SETTLE_us; noise Vpp not nV/rtHz.

## Do not

- Invert `_dmm_volt` for RS1G14.
- Reclassify leftover 13.
- Fill `imported_input_off_leakage`.
- Hammer NI-VISA / live USB 218 skips.

## Goal

OPEN.
