---
keywords: check-all-parts, sim, 157, charmap, screenshot, tp, gbw, vos, scaffold, rs0302
main_idea: SIM-ran every non-scaffold enabled TestSpec for all parts yaml: 157/157 OK. TP crashed on Windows because logic_tests called a Chinese screenshot demo. OVP raise-then-tighten still in psu_setup. rs1g14 input_off_leakage is still a Path C scaffold; rs0302 has no tests.
---

# 2026-09-14 All-parts SIM (original TestSpecs)

`python -m ate.core.check_all_parts` now SIM-runs keep+MSO enabled ids per `ate/config/parts/*.yaml` (sleep patched, auto-continue). Original bodies: logic wraps -> root `logic_tests.py`, Ariff DC, LDO, opa_tests.

First pass 141/157. 16 fails were Windows cp1252 `print` of approx-equal / Chinese, not bad recipes:

- `logic_tests.test_tp` called `scope_setup.screenshot()` which printed a Chinese demo and opened a second AutoCapture. Now a no-op; live PNGs stay `capture_scope_png`.
- GBW/VOS prints used non-ASCII. ASCII now; runner also `stdout.reconfigure(errors=replace)`.

Second pass: **SIM 157/157**, 25 parts, yaml=26. Stub `rs0302` (empty enabled_tests). Scaffold skip: `rs1g14:input_off_leakage` (Path C, not filled).

USB live of every SKU is not this check: needs DUT + Continue. MSO USB 0x0515 still skipped; lm358/rs358/rs8551 MSO tests are SIM-only on this bench until a working MSO.
