keywords: rs1gt34, automation-template, icc, icct, dut-scale, n>2, IDD_SAMPLE, INPUT_A_V, leftover-honest
main_idea: Automation template is 21 per-DUT xlsx (ICC/ICCT/IL/VIX/VOH/VOL x DUT 1-3). Path B keeps one Version book, stamps DUT, copies template columns (INPUT_{pin}_V, IDD_uA, IDD_SAMPLE1-n), and scales n>2 via AWG CH1/CH2 + PSU CH3 / Continue. Do not copy template 0-5.6 ICC or ICCT 3.0-5.5 as default.

Template vs Path B:
- ICC: template VCC 0-5.6 / 0.1, 114 rows, INPUT_A_V + 5 samples. Path B default named; picture opt-in step 2.0-5.5. Same IDD topology (AWG DC, 2s/1s/5 avg).
- ICCT: template 3.0-5.5 A=3.4 limit 500. Path B ICCT vcc 5.5 only (picture). Limit 500 from YAML Full.
- IL = Path B `ii`. VIX = `input_threshold`. VOH/VOL already Path B tables.
- 3 DUT files = sample_col. Runner `dut_indices` + Setup DUT count 1-16. golden_auto orphan if split 21 xlsx.

n-input: `_icc_drives` no longer raises n>2. n=3 (RS1G97) AWG CH1/CH2 + PSU CH3. n>3 pops extra pins and Continue-rewires. leftover-honest: golden `test_supply_current` docstring says 4 A:B states but loop only CH1 A.
