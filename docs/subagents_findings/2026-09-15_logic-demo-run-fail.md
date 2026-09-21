---
keywords: logic, demo, start, runPollActive, waitForRunComplete, run_epoch, worker-restart, mapping-empty, bench_preflight, demo_corners, dual_channel, busy, missing-instruments
main_idea: After worker restart mid-START, UI waitForRunComplete never completes (run_epoch reset) so runPollActive blocks DEMO and RUN. Ghost mapping {} also breaks USB START. demo_corners and dual_channel are not the cause.
---

PREFLIGHT: PARTIAL. Reuse `2026-09-15_sim-reprove-after-walker.md`, `2026-09-15_live-usb-walk-ignore-dmm.md`, `2026-09-15_a14-recipe-canvas.md`.

# Logic DEMO / RUN failure path (2026-09-15)

## Operator report

- Family: **logic**
- **DEMO** and **RUN** both fail
- Last **worker restart interrupted a busy START**

## Evidence

### Worker log (`ate/worker/last_worker.log`)

- Tail is RPC access lines only; no application-level `Runner busy` / `Missing instruments` text (worker does not tee `_log` to this file).
- One `ConnectionAbortedError` on RPC write (client disconnect during poll), not a run failure.

### RPC `session_status` (prior sitting + code)

Could not re-probe live RPC this pass (shell wrapper broken on host). Prior finding `2026-09-15_live-usb-walk-ignore-dmm.md` recorded:

- `busy=false`, `pending=null`, `open=true`, **`mapping={}`** (ghost USB session)

Worker exposes: `busy`, `run_epoch`, `run_error`, `mapping`, `sim` (`ate/worker/server.py:608-627`).

### DEMO handler (`ate/ui/web/app.js:5248-5277`)

1. `requireWriteOperator()` -- fails if operator is All / Kevin / ATE (`467-476`)
2. `bench_preflight` -- if `pre.mode === "usb"`, **returns early** with notice; no SIM open (`5259-5266`)
3. `applyDb()` then `open_session({ sim: true })` (`5268-5269`)
4. `startInstrumentRun(ids, { autoContinue: true })` (`5274`)

### START handler (`app.js:5281-5316`)

1. Guards: tests, DUTs, `sessionOpen`, **`runPollActive`** (`5282-5287`)
2. SIM + USB preflight mismatch notice (`5299-5308`)
3. `startInstrumentRun(ids)` -- no auto-continue

### `startInstrumentRun` / poll (`app.js:5318-5410`)

- Sets **`runPollActive = true`** before `run_sequence_async` (`5337`)
- `epoch0 = before.run_epoch` (`5338-5339`)
- `waitForRunComplete(epoch0)` exits only when **`epoch > startEpoch && !busy`** (`5400-5405`)
- On worker restart, **`run_epoch` resets to 0** (`ate/core/runner.py:239`, `302-306`) while UI still holds old `startEpoch` -> poll never completes (up to 3600 s at 250 ms)
- Meanwhile **`runPollActive` stays true** -> DEMO/START show **"Run already in progress"** (`5287`, `5320`)

### Runner `run_sequence` (`ate/core/runner.py:446-1032`)

- `Runner busy` if `_busy` and not async reclaim (`451-452`; worker `run_sequence_async` `682-683`)
- `Open Session first` if `_instr is None` (`463-464`)
- DEMO sets `gate.auto_continue` from params (`461`, `468-469`; `ate/fixture/operator.py:42-50`)
- Per-test fail: `Missing instruments: [...]` when `required_instruments - available` (`1075-1094`)
- SIM `available_devices()` = full `inst_map` keys PSU/AWG/MSO/DMM (`ate/instruments/session.py:61-62`)

### Ghost USB session (`runner.py:357-369`, `app.js:4819-4847`)

- `open_session()` without Discover can open with **`mapping {}`**
- `sessionOpen=true` enables START button (`4121-4122`)
- RUN then fails each test with **Missing instruments** (empty `inst_map`)

## Ruled out

### `demo_corners` on `load_family("logic")`

- `register_recipe_specs` adds one TestSpec; `dual_channel=False`, `required_instruments={PSU,DMM}` (`ate/core/recipe_walk.py:382-424`)
- Called after package import; exceptions swallowed but registration is straightforward (`registry.py:245-250`)
- `check_recipe.py` expects `demo_corners` after `load_family(logic)` -- not a duplicate-id breaker
- Does **not** explain DEMO/RUN both blocked before `run_sequence_async`

### `dual_channel` / CHA-only tick

- **All** logic `TestSpec` registrations set `dual_channel=False` (`wraps.py`, `ariff_dc.py:960`, etc.)
- `dual_mode = any(...)` is false for LOGIC batches -> `mode_chans = [channels[0]]` only (`runner.py:635-636`)
- CHB not ticked does **not** hang logic on channel_change

## Root causes (ranked)

1. **UI stale `runPollActive` after worker restart mid-START** -- `waitForRunComplete` waits for `run_epoch` to increase, but restarted worker resets epoch to 0 (`app.js:5397-5410`, `5338-5339`; `runner.py:239`, `302-306`). DEMO and RUN both hit `runPollActive` guard (`app.js:5287`, `5320`).

2. **Ghost USB session `mapping {}`** -- prior `session_status` open with empty map (`live-usb-walk-ignore-dmm`). USB START fails `Missing instruments` (`runner.py:1075-1094`). DEMO would replace with SIM **if** #1 is cleared (`app.js:5269`).

3. **Secondary: `bench_preflight` `mode=usb` blocks DEMO** when any *IDN is seen (`app.js:5259-5266`, `discovery.py:401`). Operator must use Discover -> Open Session -> START instead of DEMO.

## Smallest fix

**Code (one place):** In `waitForRunComplete` (`app.js:5397-5410`), after ~10 polls (~2.5 s), if `!st.busy && st.run_epoch <= startEpoch`, throw a clear error (e.g. "Worker restarted during run -- Ctrl+F5 then DEMO") and let `finally` clear `runPollActive`. Optional: at DEMO/START entry, if `session_status` reports `!busy`, reset `runPollActive`.

**Operator now (< 2 min):** Ctrl+F5 -> confirm run pill not "running" -> click **STOP** if needed -> **DEMO** (not START on ghost USB session). If DEMO still blocked by USB notice, use **Open SIM** then START, or unplug ghost USB and DEMO again.

## Checks (not run this pass -- shell blocked)

- `python -m ate.core.check_sim_run` (logic RS1G07 path proves SIM DEMO works when UI not wedged)
- `python -m ate.core.check_recipe` (demo_corners registration)
