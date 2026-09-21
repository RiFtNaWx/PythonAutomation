---
keywords: a10-t01, epic-a10, lim, rs2323, open-inventory, rs1g07, rs1g14, level-stub, f17, continue-gate
main_idea: Lim is a real builtin family with RS2323 campaign (4 current tests, Continue via pause_hook). Open inventory check covers Lim + Logic RS1G07/14 + Level stub. UI rail must include Lim in HTML or renderFamilyRail must inject missing builtins.
---

# 2026-09-03 A10 Lim RS2323 + open inventory (implemented; R-0003 not self-closed)

## What shipped

- Builtin `lim` -> `ate.tests.lim`; part `rs2323.yaml`; campaign `#Test_Database/Lim/RS2323/MSOP/Version_1`
- Tests: `iplus`, `leakage_off`, `leakage_on`, `input_leakage` (PSU+DMM; no `import Lim.*`; no stdin `input(`)
- Logic `rs1g07` / `rs1g14` campaigns reuse Ariff DC ids; Level `#Test_Database/Level/Stub/...` empty suite
- Check: `python -m ate.core.check_open_inventory`

## Verify evidence (implementer)

```
python -m ate.core.check_family_load
# OK opamp=17 logic=12 lim=4 restored=17 ...

python -m ate.core.check_open_inventory
# OK open-inventory: Lim RS2323 + Logic RS1G07/14 + Level stub

python -m ate.core.check_logic_campaign
# OK
```

Browser `http://127.0.0.1:5174/?v=20260903g`: Lim brand + Apply RS2323 -> 4 tests `LIM_RS2323`; Logic RS1G07 -> 4 DC ids; OpAmp restore -> 17 + gain panel visible.

## Trap

`renderFamilyRail` used to skip all builtins when adding extras. If `index.html` lacked a Lim button, known `lim` never appeared. Fix: HTML Lim button + rail injects missing known builtins. Cache-bust `app.js?v=20260903g`.

## Out / parked

RS0204 (no source); Lim `threshold_tests` (RS1G126); cpd/cin; Level suite; DataLogger replace. Independent R-0003 still required (Grok 4.5 high).
