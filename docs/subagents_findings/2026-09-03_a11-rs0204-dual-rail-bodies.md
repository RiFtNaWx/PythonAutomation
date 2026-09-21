---
keywords: a11, rs0204, dual-rail, logic_test.py, soo-dispatcher, vcca, vccb, f19
main_idea: Downloads/logic_test.py is a broken Soo dispatcher (missing import, TypeError IDD, wrong names). ATE now runs dual-rail RS0204 bodies matching the 16 workbook sheets. Do not import Soo.
---

# 2026-09-03 RS0204 dual-rail bodies (F19)

PREFLIGHT: HIT. Reuse A11 campaign. Author file: C:\\Users\\OoiJianHong\\Downloads\\logic_test.py

## Author file failures

- `from Soo.logic_tests import test_input_thresholds` -- Soo has `#def test_input_thresholds` only
- `test_supply_current(instr, vcca, vccb)` -- Soo signature is `(instr, vcc)`
- Dispatcher names != lab report (no VIH/VIL/Tsu/fmax/tr/Tsk/tw)
- Single-rail PSU CH1 only; RS0204 needs VCCA and VCCB

## Shipped

- `ate/tests/logic/rs0204.py` dual-rail (CH1=VCCA, CH2=VCCB)
- yaml vcca=1.8 vccb=3.3; rails_from_params refuses VCCA > VCCB
- Tsu/Th = datasheet ten/tdis; Cpd = DMM pin Cio
- Downloads/logic_test.py rewritten to fail closed with the map

## Verify

```
python -m ate.core.check_family_load
# OK opamp=17 logic=28 lim=4 ...
python -m ate.core.check_logic_campaign
# OK logic-campaign: RS29511 + RS1G08 + RS0204
python -m ate.core.check_mapped_tests
python -m ate.core.check_open_inventory
```

Worker 0.2.10 ping. Apply RS0204: list_tests=16, mapped_coverage n_map=16 missing_specs=[], fixture LOGIC only. Console 5174: Logic / RS0204 / TSSOP14, coverage 16/16, LOGIC accordion 16 tests, no G11. START stays disabled until Open Session.
