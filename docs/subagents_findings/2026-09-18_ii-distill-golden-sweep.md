keywords: rs1gt34, ii, input-leakage, distill, 2^n, awg, no-trac, no-power-off, leftover-honest
main_idea: Distill golden test_input_leakage_sweep into Path B ii. Keep 2^n AWG 0/5.5 and 5 DMM samples. Drop TRAC, power_off-per-VCC, IDD_uA, ovp=vcc_stop. GT34 n=1 is 2 combos. RS1G08 n=2 is 4. Default named; this START overlays 0-5.6/0.1 (VCC=0 is Ioff-like).

PREFLIGHT: HIT
reuse: goldens/ariff/logic_tests.py, docs/subagents_findings/2026-09-18_ii-named-idd.md
spawn: skip
