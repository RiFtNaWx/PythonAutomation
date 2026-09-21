---
keywords: family-rail, campaign, component, set_db_context, logic_tests.py, soo, rs29511, auto-switch
main_idea: Changing Test Database Component/Part/Package/Version now switches Family (OpAmp/Logic/Lim/Level). Downloads/logic_tests.py is Soo RS29511, not RS0204.
---

# 2026-09-03 Campaign directory switches Family

PREFLIGHT: HIT. Reuse A11 dual-rail + A09 Logic PaaS. Spawn: skip.

## Downloads/logic_tests.py

Soo RS29511 suite. Live `test_supply_current(instr, vcca, vccb)` would TypeError old wrap. `test_input_thresholds` calls `setup_ramp` with wrong args. Not RS0204. ATE wrap `_invoke_legacy` now accepts both IDD signatures. Do not copy this file into `ate/`.

## UI / worker

- `family_for_component` in `ate/core/database.py`
- `set_db_context` loads that family when idle
- Component/Part/Package/Version change auto-applies campaign + Family rail
- Family rail click restores last campaign in that component folder

## Verify

```
python -m ate.core.check_mapped_tests
python -m ate.core.check_family_load
```

Worker 0.2.11. Ctrl+F5. Change Component Logic <-> OpAmp: brand and Family rail follow; last Logic campaign restores RS0204.

