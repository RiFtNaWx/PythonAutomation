---
keywords: junior, ron, vcom, ton, toff, clk_q, rs2323, rs1g74, analog-switch, dff
main_idea: RS2323 RON now sweeps VCOM 0/half/V+ at 10 mA CC. Path B ton_toff uses in-repo measure_delay. RS1G74 clk_q is CLK-to-Q, not AND tp. SIM 216/216. Not junior-100%.
---

# 2026-09-14 Analog-switch TON + DFF CLK-Q

PREFLIGHT: PARTIAL. Reuse: 2026-09-14_junior-ron-class-skus. Spawn: skip.

## This sitting

1. `ron` VCOM sweep: CH1=V+, CH3=VCOM (0 / 0.5 / 1.0 * VCC), CH2 CC 10 mA, DMM Kelvin. Matches lab Icom=-10 mA / VNO 0-to-V+. Limits still typ 0.6 (PDF min/max image).
2. Path B `ton_toff`: `scope_setup.measure_delay` FFDelay/RRDelay (same tokens as logic tpd). Stamps TON_ns / TOFF_ns typ 50 from banner. SIM DELAY = 50 ns when AWG ON.
3. Path B `clk_q` on RS1G74: AWG CH1=CLK square, CH2=D=VCC, MSO CLK->Q. Combinational vih_vil/voh_load stay banned.

## Proof

```
python -m ate.core.check_add_test
python -m ate.core.check_family_load
python -m ate.core.check_stimulus
python -m ate.core.check_specs_datalog
python -m ate.core.check_all_parts
```

SIM **216/216** parts=25 stub `rs0302`. switch=6 logic=35. Does not prove USB 0.6 ohm or 50 ns.

## Leftover-honest (goal still open)

- Analog-switch Con/Coff/tBBM/Vth/BW/ISO; rON min/max PDF image
- RS164 serial-shift; RS1G123 monostable pulse width
- RS0302 empty suite
- OpAmp PSRR/CMRR/AOL/EMIRR/PowerOn mapped captures
- Excel VOX unique Vcc rows only; RS0204 Icc/VOH empty/grid
- USB START of every SKU
