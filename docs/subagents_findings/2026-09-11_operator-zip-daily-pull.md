---
keywords: installer, zip, eugene-console, rift, auto-pull, ff-only, sharepoint, onedrive-sync, pin-1
main_idea: Operators get START.bat zip; vibe-coders clone -b eugene-console on RiFtNaWx. Daily git pull is ff-only and skips a dirty tree. Results live in the SharePoint-synced #Test_Database; OneDrive is the upload.
---

# 2026-09-11 Operator zip + safe daily pull + central cloud

PREFLIGHT: HIT. Reuse: ate-try-packet, app-vs-dev-cloud-db, sharepoint-rs622-photos, central-run-ledger. Spawn: skip.

## Send to people

- App: `ATE_Console_Try_YYYY-MM-DD.zip` (Desktop + dist/, also GitHub Release when `gh` can attach it)
- Clone: `git clone -b eugene-console https://github.com/RiFtNaWx/PythonAutomation.git`

## Auto-pull (clone only)

`ate/core/sync_repo.py` from Cursor folder-open and `run_ate_app.bat`.
Dirty working tree -> fetch only. Clean -> `git pull --ff-only`. Never reset --hard.
Operator zip sets `ATE_APP_ONLY=1` so it does not pull.

## Cloud results

Write path = `cloud_db.txt` OneDrive folder. https in `sharepoint.url`. No Graph/A13. OneDrive syncs `sessions/` after START.

## Proof

```
python -m ate.core.check_sync_repo
python -m ate.core.check_ui_contract
python -m ate.core.check_cloud_db
python pack_ate_console.py --check
```
