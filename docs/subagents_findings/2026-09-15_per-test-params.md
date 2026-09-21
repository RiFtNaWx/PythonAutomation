keywords: test-params, overlay_for, run-conditions, sweep, write, version, customisable, iplus, set-context
main_idea: Shared Setup Run-conditions VCC bar is gone. Each Test program row has Parameters + Write to this Version `_manifest/test_params.yaml`. Write must pin Setup campaign or leftover worker context steals the yaml. START uses RunParams.overlay_for(test_id).

# Per-test Parameters (customisable ATE)

Operator ask: remove the YAML VCC (V) Run conditions panel; every test edits its own sweep/specs like imported location + Write.

## Where

- `ate/core/database.py` `load_test_params` / `save_test_params` -> `_manifest/test_params.yaml`
- `ate/core/runner.py` `RunParams.overlay_for` in `_run_one` (one blast-radius hook, not a second runner)
- `ate/worker/server.py` `set_test_params` pins `set_context` from payload then saves
- `ate/ui/web` Test program card: visible Parameters + Write. No `#panel-run-conditions`, no global `#sweep-panel`.

## Behaviour

- Sweep fields follow `stimulus.sweep` (vcc / freq / vcom / vin). Spec min/max/typ editable.
- Write persists this operator Version only. Payload includes Setup picker so a later `set_db_context` from another tab cannot steal the yaml.
- START calls `applyDb` then sends `test_params`; overlay_for applies per TestSpec.
- Unticked tests: `Select tests -- standard defaults apply.`
- Analog-switch yaml corners still used when VCC start/stop/step stay 0 / 5 / 0.5.

## Trap

2026-09-15: Write Iplus on Analog SW / RS2323 / SeeLim wrote `Logic/RS1G126/.../JianHong/.../test_params.yaml` because worker `get_context()` had drifted. Fix: pin campaign on `set_test_params`. Stolen file deleted.

## Checks

`python -m ate.core.check_ui_contract`
`python -m ate.core.check_walk_order`
`python -m ate.core.check_stimulus`
`python -m ate.core.check_sim_run`
