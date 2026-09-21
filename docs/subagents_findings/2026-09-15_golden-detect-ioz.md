---
keywords: detect, wrap, test_parameter, input_threshold, instr, see-lin, ioz, golden-roots, ariff
main_idea: Detect BLOCKED "missing instr" was a false positive -- test_parameter is a config helper, test_input_threshold takes psu/dmm. Scanner now skips helpers, accepts VISA handles, treats _prompt as input(), aliases filled goldens. Path B ioz for RS1G125/126 from See Lin.
---

# 2026-09-15 golden wrap scanner + See Lin IOZ

## Why the UI looked dumb

| Detect row | Actual golden | Fix |
|------------|---------------|-----|
| PARAMETER Eugene opa_tests.py:5 | `def test_parameter()` returns TEST_CONFIGURATIONS | skip helper, not a test |
| PARAMETER Soo logic_tests.py:7 | same helper | skip |
| INPUT_THRESHOLD Lim threshold_tests.py:174 | `def test_input_threshold(psu, dmm, logger, ...)` real VIH/VIL | accept psu/dmm; alias to `input_thresholds` / `vih_vil` |

See Lin `test_ioz` calls `_prompt` -> `input()`. Direct AST on `test_ioz` missed that. Now block via helper. Path B `ioz` in `ariff_dc.py` uses `pause_hook`.

## Roots added

`ate/config/golden_roots.yaml`: Ariff v1 + LDO/Logic/Level drops, See Lin Repo, Eugene Repo, LabAutomation_14.7 Downloads copy. Missing dirs still skip.

Ariff LDO / Logic / LevelTranslator folders are README-only. Real Python is `LabAutomation_v1 - Copy` (already mapped as LDO/logic TestSpecs: iq/vinmin/lir/lor/ioutmax/enable_current + Ariff DC).

## Check

```
python -m ate.core.check_test_detect
python -m ate.core.check_add_test
python -m ate.core.check_family_load
python -m ate.core.check_stimulus
```
