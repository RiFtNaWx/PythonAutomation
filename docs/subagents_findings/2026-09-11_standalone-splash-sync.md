---
keywords: splash, pythonw, silent-launch, sync-repo, standalone, loading
main_idea: Double-click START/run_ate_app opens a loading splash, runs first-of-day git sync via RPC, hides python consoles (pythonw + CREATE_NO_WINDOW). Zip skips git. Not a Tauri rewrite.
---

# 2026-09-11 Standalone splash + daily sync

PREFLIGHT: HIT. Reuse operator-zip-daily-pull, first-run-progress-board. Spawn: skip.

## Start path

`run_ate_app.bat` -> `pythonw -m ate.ui.launch` -> hidden worker 8766 + UI 5174 + browser.
Splash `#boot-splash` until ping + `sync_repo` (stamp = first of day). Dirty tree never overwritten.

## Proof

```
python -m ate.core.check_launch
python -m ate.core.check_sync_repo
python -m ate.core.check_ui_contract
```
