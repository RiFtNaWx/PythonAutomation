keywords: rs1gt34, icc, awg, golden-idd, step-0.1, leftover-honest
main_idea: Path B ICC now drives VI on AWG CH1/CH2 (golden test_supply_current IDD), not PSU CH3. PSU_MSO pin_drive A=CH3 stays for VIH. GT34 n=1: AWG CH1=A, high=this VCC, 2.0-5.5 step 0.1 overlay. Live 72-pt still needs Open Session.

PREFLIGHT: HIT
reuse: docs/subagents_findings/2026-09-18_icc-step-dmm-113.md
spawn: smaller-executor

## What was wrong

The pasted Ariff `test_supply_current` IS the IDD pattern: PSU CH1=VCC, AWG DC on inputs, DMM series, 0.1 VCC step. Path B ICC ignored AWG because GT34 `pin_drive.A=PSU CH3` (VIH PSU_MSO) and TestSpec ICC only required PSU+DMM.

## Fix (shared runner, not a GT34 fork)

- `_icc_drives`: remap icc pins to AWG CH1 then CH2. n=1 GT34 = CH1=A. n=2 1G08 = A+B.
- `_run_icc` / `_run_delta_icc` use those drives + `set_output_load INF`.
- High = `logic_volts` = this VCC, not 5.5 at VCC=2.0.
- TestSpec icc/delta_icc require AWG.
- wire_map icc/delta_icc: PSU CH1 + AWG CH1, not CH3.
- YAML pin_drive A stays PSU CH3 for VIH.

Do not port: vcc 0-5.6, TRAC:CLE, input(), setup_dc(psu), 5.5 V on A at every VCC, AWG CH2 on a 1-input buffer.

## Leftover-honest

- check_logic_dc still ImportError `infer_pass_mode` (specs.py). Pre-existing; not this ICC patch.
- USB mapping empty after last restart. 72-pt live not proven this turn. Operator Discover + Open Session then START icc.
