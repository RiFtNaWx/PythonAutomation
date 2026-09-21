---
keywords: operator-folder, kevin, ate, plus, package, sweep-panel, vcc, freq, seelim, rs2323
main_idea: Setup Operator folder lists only people with a folder on this Component/Part/Package. Kevin and ATE never appear. Plus on package/operator opens pick-existing or add-new. Sweep boxes pop only for ticked sweep tests.
---

PREFLIGHT: PARTIAL. Reuse: 2026-09-14_add-person-channels, 2026-09-14_delta-vcc-cin-freq, 2026-09-14_first-run-name-multi-sku. Spawn: skip.

## Operator / package

`refreshDbCascades` used to concat every `owners.yaml` label into `#db-operator`, so AnalogSwitch / RS2323 / MSOP showed Kevin, ATE, Ariff, LaLa. Default list is now disk operators for that package only. `mergeInventoryIntoTree` no longer injects the current person into every tracking SKU.

Kevin / ATE / All / `_unassigned` are `hiddenOperatorName`. Writes blocked in `database.require_write_operator`. Header `#owner-select` keeps All, drops Kevin/ATE.

`#btn-plus-package` / `#btn-plus-operator` open `#campaign-plus-modal`: pick existing or type new. Existing person/package -> `ensure_product` this SKU. Brand-new person -> existing `#add-operator-modal` / `provision_operator`.

## Sweep

`#sweep-panel` hidden until a ticked test has `stimulus.sweep` (vcc / freq / vcom / vin). Cards name each selected sweep test. VCC 0/5/0.5 still default; Delta Supply uses that and AWG CH1 then CH2. CIN uses `freq_start/stop/step` (default 1/10/4 MHz -> 1/5/10 MHz). Analog-switch yaml corners stay unless the operator changes VCC boxes.

## Check

```
python -m ate.core.check_ui_contract
python -m ate.core.check_operator_tree
python -m ate.core.check_progress
python -m ate.core.check_walk_order
python -m ate.core.check_stimulus
```

Ctrl+F5 (`?v=20260915oppkg1`). Worker idle-restart after runner/stimulus/tests.
