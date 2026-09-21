---
keywords: junior, con_coff, tbbm, pulse_width, serial_shift, clk_q, rs2323, rs164, rs1g123
main_idea: Path B analog-switch CIN/CON/COFF + tBBM, RS1G123 pulse_width, RS164 clk_q + 8-clock serial Q7. SIM 221/221. Not junior-100%.
---

# 2026-09-14 Switch C/tBBM + pulse + serial

PREFLIGHT: PARTIAL. Reuse: 2026-09-14_switch-ton-dff-clkq.md. Spawn: skip.

## This sitting

1. RS2323 `con_coff`: DMM CAP CIN (V+ off), CON (IN=V+), COFF (IN=GND). Stamps CIN_pF / CON_pF / COFF_pF. No invented min/max.
2. RS2323 `tbbm`: AWG square on IN, MSO NO vs NC `measure_delay` RRDelay/FFDelay, stamp TBBM_ns = min(abs)*1e9.
3. RS1G123 `pulse_width`: `setup_pulse` + `measure_single` PWIDth. Board RC. No invented min/max.
4. RS164 `clk_q` (CLK->Q0, strap B=/MR=VCC) plus Path B `serial_shift` (8 CLK then DMM Q7 high/low). Not combinational VOH.
5. RS2227 still banned from RS2323-pinout ron/ton/con/tbbm.

## Proof

```
python -m ate.core.check_add_test
python -m ate.core.check_family_load
python -m ate.core.check_stimulus
python -m ate.core.check_specs_datalog
python -m ate.core.check_all_parts
```

SIM **221/221** parts=25 stub `rs0302`. switch=8 logic=37. Does not prove USB pF / ns / Q7 VOH.

## Leftover-honest (goal still open)

- Analog-switch Vth / BW 110 MHz / ISO / XTalk; rON min/max PDF image
- RS164 `tp` wrap is still combinational-shaped; serial_shift is Q7 only (not Q0-Q6 grid)
- RS0302 empty suite (do not copy RS0204)
- RS74AUP1G07 no PDF VOH/VOL
- OpAmp PSRR/CMRR/AOL/EMIRR/PowerOn = mapped captures. Eugene `test_SSR` is delay + `input()`, not PSRR dB. Noise = 0.1-10 Hz Vpp. ISC missing.
- Excel unique VOX Vcc rows only; RS0204 Icc/VOH empty/grid. Probe live xlsx.
- USB START of every SKU
- Path C `input_off_leakage` scaffold must stay unfilled and not enabled
