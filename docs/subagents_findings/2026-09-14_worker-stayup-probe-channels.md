---
keywords: worker, watchdog, tray, high-priority, notice-banner, probe-channels, CHA, CHB, logic, supervisor
main_idea: Launch.py now stays up as a high-priority supervisor with a hidden tray icon and respawns :8766 if ping dies. Channel B is off for Logic/LDO/switch unless part yaml channels: [A, B].
---

# Worker stay-up + probe channels (2026-09-14)

## Why the worker was "down"

`ate.ui.launch` used to spawn worker+UI, open the browser, then **return**. `START.bat` / `run_ate_app.bat` exited. The worker was an orphan. Task Manager / crash / `pythonw` death left splash `Could not start`. Nothing respawned :8766.

## What changed

- `ate/ui/launch.py` stays resident (pythonw). `watch_forever` pings every 4s and respawns worker/UI. Child processes get `CREATE_NO_WINDOW | HIGH_PRIORITY_CLASS` (not REALTIME).
- Hidden tray (`ate/ui/tray.py`, ctypes `Shell_NotifyIcon`, `assets/ate.ico`). No balloon popups. Left-click / menu Open console. Restart worker only if `session_status.busy` is false. No Quit item -- Task Manager is the hard stop.
- Second START.bat does not open another browser tab when :5174 is already listening. Duplicate supervisor pid is skipped.
- Worker bind: if :8766 already answers ping, duplicate process exits 0. `serve_forever` recovers from accept errors. `WORKER_VERSION` 0.2.37.
- `restart_ate_worker.bat` kills only :8766, waits for supervisor respawn, falls back to `--worker-only`.
- Standalone operator path uses `#notice-banner` instead of `window.alert` for Discover empty / DEMO USB / START gates.
- Probe CHA/CHB: `ate.core.specs.probe_channels_for_part`. Part yaml `channels:` / `datasheet.channels` wins. Else OpAmp A+B, Logic/switch/level/power A only. `identity.probe_channels` + runner `resolved_channels()` clip CHB. Setup disables the B checkbox.

## Not this

- Cannot survive Task Manager End Task on the supervisor itself (watchdog is that process).
- Does not scrape en.run-ic.com for pin count. Override with yaml `channels: [A, B]` when a Logic SKU is dual-probe.
- Setup More engineer `alert()` leftovers stay (wrap / import). Daily Discover/DEMO/START do not.
