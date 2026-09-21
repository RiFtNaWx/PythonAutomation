---
keywords: junior, ron, analog-switch, rs2323, rs164, rs1g74, rs1g123, cin, cpd, ioff, excel-probe, leftover-honest
main_idea: Path B RS2323 RON stamps RON_ohm via DMM Vdrop / 10 mA CC (typ 0.6 only). DFF/shift/mono now run cin/cpd/ioff, not combinational VOH. SIM 214/214. Excel leftover confirmed on live zip xlsx. Not junior-100%.
---

# 2026-09-14 Junior RON + class-SKU input physics

PREFLIGHT: PARTIAL. Reuse: junior-production-scale, junior-values-gt-enable, leftover-honest R-0003. Spawn: skip.

## This sitting

1. Path B `ron` in `ate/tests/lim/rs2323.py`. PSU CH1=V+, CH2 CC 10 mA (`ron_force_a: 0.01`), DMM VDC Kelvin COM-NO/NC. No ohms SCPI. Limits stay typ 0.6 (PDF rON min/max still an image). RS2227 does not enable it (USB pinout).
2. RS164 / RS1G74 / RS1G123 enable existing `cin` / `cpd` / `ioff_leakage` only. Combinational `vih_vil` / `voh_load` stay banned (Q does not follow D/A without CLK; mono Q is a pulse).
3. Live `Test Reports.zip` probe (drop folder still missing):
   - RS1G08 VOX unique Vcc rows: **1.65 / 2.3 / 3.0 / 4.5** (two IOH rows at 3.0 V). Yaml 2.0 / 3.3 / 5.0 / 5.5 have no VOX row.
   - RS0204 Data Report `Icc` and `VOL` are 1x1 empty; `VOH` is 8x2 commentary, not a DUT grid. Do not invent cells.
   - RS2323 Wuxi book has a **Ron** sheet (V+=5 V, Icom=-10 mA, VNO/VNC sweep). Old numbers ~67 ohm marked incorrect. Platform RON is VCC sweep at VCOM~0, not the full VCOM grid. TON/TOFF/Con/Coff/tBBM/Vth still have no TestSpec.

## Proof

```
python -m ate.core.check_add_test
python -m ate.core.check_family_load
python -m ate.core.check_stimulus
python -m ate.core.check_specs_datalog
python -m ate.core.check_all_parts
```

SIM **214/214** parts=25 stub `rs0302`. switch=5 (ron). Does not prove USB RON ohms.

## Leftover-honest (goal still open)

- Analog-switch TON/TOFF/Con/Coff/tBBM/Vth; RON VCOM 0-to-V+ grid; rON min/max PDF image
- RS164/RS1G74/RS1G123 serial/CLK/Q recipes
- RS0302 empty suite
- RS74AUP1G07 no PDF VOH/VOL
- OpAmp PSRR/CMRR/AOL/EMIRR/PowerOn mapped captures; noise is Vpp not nV/rtHz
- Excel: VOX unique rows only; RS0204 Icc/VOH unmapped (empty/grid)
- USB START of every SKU
