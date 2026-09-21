---
keywords: junior, psrr, vth, mapped, rs622, rs2323, tp, clk_q, leftover-honest
main_idea: Mapped OpAmp psrr replaced with DC Vs-step PSRR_dB. RS2323 Path B vth. Combinational tp dropped on RS164/RS1G74/RS1G123. SIM 219/219. Not junior-100%.
---

# 2026-09-14 DC PSRR + analog Vth

PREFLIGHT: PARTIAL. Reuse: 2026-09-14_switch-c-tbbm-pulse-serial.md. Spawn: skip.

## This sitting

1. `ate/tests/opa/psrr.py` Path B: dual-rail Vs 2.5 V then 5.5 V (RS62X 7.4), AWG DC 0 V, DMM Vout, stamp PSRR_dB = 20*log10(|dVs|/|dVout|). Fixture stays ATE so slew/psrr still split. Mapped `psrr` screenshot row removed. Eugene `test_SSR` stays unwrapped (`input()` + delay).
2. RS2323 Path B `vth`: COM=V+/2, AWG DC sweep IN, DMM on NO. No invented min/max. RS2227 still banned.
3. Drop combinational `tp` wrap on RS164 / RS1G74 / RS1G123 (clk_q / serial_shift / pulse_width own those SKUs).

## Proof

```
python -m ate.core.check_add_test
python -m ate.core.check_family_load
python -m ate.core.check_stimulus
python -m ate.core.check_specs_datalog
python -m ate.core.check_sim_run
python -m ate.core.check_all_parts
```

SIM **219/219** parts=25 stub `rs0302`. switch=9. `check_sim_run` RUN PSRR (DC Vs step). SIM DMM is CMOS (Vin=0 -> 0.001 both rails) so SIM PSRR hits the 1 uV floor (~129 dB), not 93 typ. USB DMM is the real number.

## Leftover-honest (goal still open)

- Analog-switch BW 110 MHz / ISO / XTalk; rON min/max PDF image
- CMRR/AOL/EMIRR/PowerOn still mapped captures. Noise = 0.1-10 Hz Vpp not nV/rtHz. ISC missing
- RS0302 empty suite
- RS74AUP1G07 no PDF VOH/VOL
- Excel unique VOX Vcc rows; RS0204 Icc/VOH empty/grid
- USB START of every SKU
- Path C `input_off_leakage` unfilled
