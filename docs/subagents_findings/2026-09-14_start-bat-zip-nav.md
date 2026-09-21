keywords: start.bat, zip, cloud_db, onedrive, shortcut, packer, navigation, retired-sync
main_idea: SharePoint Sync + C:\Users\YOU\#Test_Database is retired. Git and zip both use START.bat. Packer packs START.bat as START.bat (not TRY_ATE rename).

# 2026-09-14 START.bat + zip navigation

## Retired
- SharePoint **Sync** button
- Drag-copy to `C:\Users\YOURNAME\#Test_Database`
- Hand-edit `cloud_db.txt` with that home path

## Current
- Add shortcut to OneDrive on Handover / Jianhong / #Test_Database
- Replace if asked, Always keep on this device
- `START.bat` writes `ate/config/cloud_db.txt`

## Navigation
- Repo + zip: `00_START_HERE.txt` + `START.bat` at the top
- `TRY_ATE.bat` is a 3-line wrapper that calls `START.bat` (git only, not in zip)
- Zip no longer ships `restart_*.bat`, `run_ate_worker.bat`, `TRY_ATE.bat`, `cloud_db.txt`, `.ps1`, `check_*.py`
- Tutorial HTML+images go in the zip under `docs/tutorial/`

## Checks
- `python -m ate.core.check_launch`
- `python pack_ate_console.py --check`
