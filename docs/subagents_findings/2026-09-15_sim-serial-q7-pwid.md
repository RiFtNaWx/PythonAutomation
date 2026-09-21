---
keywords: sim, serial_shift, q7, pwid, pulse_width, rs164, rs1g14, rfdelay, leftover-honest
main_idea: RS164 Q7_LOW no longer stamps VCC. SIM DMM follows AWG CH2 serial A when CH1 is CLK. CHAN2 PWID follows 0.5/f not 500 ns dummy. RS1G14 tPD queries RFDelay/FRDelay. Leftover 13 unchanged. Goal OPEN.
---

PREFLIGHT: PARTIAL
reuse: `docs/subagents_findings/2026-09-15_sim-chan2-oe-dc-fmax.md`, `2026-09-15_sim-stamp-must-ids.md`, `2026-09-15_sim-delay-tidle-dc.md`
spawn: skip

# SIM serial Q7 + CHAN2 PWID + invert DELAY (2026-09-15)

## Closed this sitting

1. `ate/instruments/sim.py`: CH1 SQU/PULS + CH2 DC -> DMM Y follows CH2 A (RS164 Q7). Was `return vcc` because `_BUS.func` is CH1 square. Same USB DMM READ? path.
2. SIM CHAN2 PWID follows driven src 0.5/f. Removed 500 ns dummy (same class as old 0.12 s RTime).
3. `ate/tests/logic/cmos_prop.py`: RS1G14 inverter queries RFDelay (A rise -> Y fall) and FRDelay (A fall -> Y rise). Still measure_delay USB SCPI. SIM DELAY stays two-bin leftover-honest (~50 ns).
4. Fail-closed: Q7_LOW >= 0.2*Q7_HIGH fails. PULSE_ns < 1 us fails. check_sim_run + loopback assert Q7 high/low and CHAN2 PWID. check_add_test bans `return 500e-9`.

## Proof

```
python -m ate.core.check_add_test
python -m ate.core.check_sim_run
python -m ate.core.check_all_parts
```

SIM **218/218**. physics REALIZED=205 LEFTOVER=13. `sim_stamps.json` n=218 ok=218.

File stamps: rs164 serial_shift `Q7_HIGH_V=5.0` `Q7_LOW_V=0.001`. rs1g123 pulse_width `PULSE_ns=500000` (0.5/1 kHz leftover, not 500 ns dummy).

Worker idle-restarted on 8766 after sim.py / cmos_prop. ping after restart.

## Leftover-honest (not leftover 13)

- SIM LIR_mV ~1600: no LDO model.
- LM358 SR_Vus ~5.55 vs typ 0.5: SIM 1-pole slew.
- all-GBW GBW_MHz=7.006 SIM G11 1-pole.
- rs0204 tsu/th workbook names TEN_ns/TDIS_ns.
- rs0204 FMAX_Mbps=20 AWG cap, not PDF 50.
- rs0204 TR/TF=5 ns MSO 70 MHz ceiling, not typ 6.6 ns.
- SIM DELAY two bins ~50 ns both edges (not SPICE).
- SIM pulse_width PULSE leftover 0.5/f of trigger (~500 us at 1 kHz), not board RC.
- RS1G14 VOH/VIH/VOL still SIM-buffer polarity (Y follows A). USB inverter needs A=0 for VOH. Do not fake invert in DMM without a DUT model.

## Leftover 13 (must stay; do not reclassify)

iso/xtalk 1 MHz not 110 MHz; usb_iso/usb_xtalk 1 MHz not 550 MHz; ron/usb_ron/i2c_ron 10 mA; settling SETTLE_VPP_V not 0.1% SETTLE_us; noise Vpp not nV/rtHz.

## Do not

- Fill or enable `imported_input_off_leakage`.
- Fake datasheet RC, invert VOH by flipping SIM globally, or 50 Mbps fmax.
- Reclassify leftover 13.
- Hammer NI-VISA / live USB 218 skips.

## Goal

OPEN.
