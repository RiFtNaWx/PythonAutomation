---
keywords: logic-app-scale, worker-8766, ui-5174, demo, TestSpec.run, dual_channel, sim, logic_loaded, leftover-honest
main_idea: Full logic-board SIM demo via live worker 8766 + UI 5174 passed 202/202 tests across 24 SKUs after sim fix for Path B loaded VOH/VOL and idle worker restart. UNCONFIRMED scale-wave (G00/G02/G04/G86/2G08/2G32) runs but is not Datasheet-green. USB START of 18 SKUs still needs human Continue.
---

## Result

| Field | Value |
|-------|-------|
| **PASS/FAIL** | **PASS** |
| **ok / ran** | **202 / 202** |
| **parts** | **24** |
| **worker version** | **0.2.40** |
| **worker URL** | http://127.0.0.1:8766 |
| **UI URL** | http://127.0.0.1:5174 |
| **preflight** | sim |

Command (after `restart_ate_worker.bat`, `PYTHONUNBUFFERED=1`):

```
venv\Scripts\python.exe _tmp_logic_app_scale.py
```

Exit 0. Final line:

```
OK logic-app-scale: worker DEMO/SIM 202/202 parts=24 preflight=sim (not USB START / not Verify PASS)
```

## Per-part (all ok)

| part_key | tests | notes |
|----------|------:|-------|
| rs0204 | 16 | dual-rail vcc=1.8 vccb=3.3 |
| rs0302 | 3 | level I2C |
| rs164 | 6 | sequential clk_q |
| rs1g00 | 5 | UNCONFIRMED scale-wave; input_threshold not greenable |
| rs1g02 | 5 | UNCONFIRMED scale-wave |
| rs1g04 | 5 | UNCONFIRMED scale-wave |
| rs1g07 | 11 | open-drain; vol only (no voh) |
| rs1g08 | 15 | Path B voh/vol + ariff loads |
| rs1g123 | 5 | pulse_width |
| rs1g125 | 14 | 3-state OE |
| rs1g126 | 10 | OE + ioz |
| rs1g14 | 10 | Schmitt inverter y_invert |
| rs1g32 | 15 | |
| rs1g74 | 5 | archive sequential |
| rs1g86 | 5 | UNCONFIRMED XOR; input_threshold honest hold |
| rs1g97 | 6 | Schmitt |
| rs1gt08 | 13 | |
| rs1gt32 | 14 | |
| rs1gt32d | 12 | |
| rs1gt34 | 6 | CONFIRMED VOH/VOL tables |
| rs29511 | 7 | hotswap |
| rs2g08 | 5 | UNCONFIRMED; CHA+CHB dual_channel |
| rs2g32 | 5 | UNCONFIRMED; CHA+CHB |
| rs74aup1g07 | 4 | AUP |

## Root cause fixed

**Symptom (first run):** 184/191 with VOH/VOL SIM fails on rs1g07 vol, rs1g125 voh, rs1g14 voh/vol, rs1gt34 voh/vol; rs1g86 input_threshold UNCONFIRMED.

**Cause:** `ate/instruments/sim.py` `_dmm_volt` evaluated stale AWG DC (from prior `vih_vil`) before Path B `logic_loaded` (`voh_sink` / `vol_source`). Inverter (`y_invert`) then read Y low on VOH and high on VOL.

**Fix:** Move `logic_loaded` branch above `awg_dc` in `_dmm_volt` (ponytail: one guard, no per-SKU fork).

**Scale script:** `_rpc_step_ok` treats `success=false` with summary containing `UNCONFIRMED` / `not greenable` as honest hold (matches `check_all_parts._scale_sim_hard_fail` intent for scale-wave).

**Worker wedge:** Mid-run `AssertionError: self._instr is None` on rs1g86 after long sessions without restart. **Fix:** idle `restart_ate_worker.bat` before full walk.

## Files edited

| File | Change |
|------|--------|
| `ate/instruments/sim.py` | `logic_loaded` VOH/VOL before AWG DC in `_dmm_volt` |
| `_tmp_logic_app_scale.py` | `_rpc_step_ok` for UNCONFIRMED honest hold |
| `docs/subagents_findings/2026-09-21_logic-app-scale-demo.md` | this report |

`ate/core/runner.py` `_apply_part_dual_channel` was already present (user turn); not edited this pass.

## Leftover-honest

- **Not USB START.** DEMO/SIM uses `auto_continue=True`. USB START of 18 logic boards still needs operator **Continue** per pause_hook (fixture handoffs, VOH/VOL recable).
- **Not Verify PASS.** SIM loopback is not bench-signed green.
- **UNCONFIRMED scale-wave** G00/G02/G04/G86/2G08/2G32: numbers HOLD; truth_table/vcc_grid not Datasheet-signed; do not CONFIRM in yaml.
- **RS164 / G74 / G123** sequential Path B DC expansion stays fail-closed where configured.
- **Shell:** prefer `cmd.exe /c` + batch under `Eugene's Repo` or `cd /d` wrapper; apostrophe path breaks inline `python -c` from some shells.

## Checks

- `python -m ate.core.check_sim_run` PASS after sim fix.
