---
keywords: handover, cloud-db, choose-folder, pack-console, onedrive-shortcut, start-no-block, team-onboard
main_idea: START never blocks when #Test_Database is missing. Discover accepts Core AE vs AE FAE nested OneDrive shortcuts. Setup Choose folder writes cloud_db.txt. PACK.bat + GitHub Actions build the operator zip.
---

# 2026-09-21 Cloud DB no-block + pack pipeline

PREFLIGHT: HIT on 2026-09-14_sharepoint-root-looks-stale, 2026-09-14_local-testdb-onedrive-shortcut, CLOUD_TEST_DATABASE.md. Spawn: skip.

## What changed

- `START.bat` always launches. `require_cloud_db` exits 0 and prints WARN if the folder is missing.
- `paths.discover_onedrive_test_db` walks known nested shortcut layouts and scores OneDrive over the retired home drag-copy.
- Worker RPCs `cloud_db_status` + `pick_cloud_db`. Setup `#btn-pick-cloud-db` Choose folder.
- `PACK.bat` + `.github/workflows/pack-console.yml` (artifact on push, Release on tag).
- New team page: `docs/handover/TEAM_ONBOARD.md`.

## Do not

- Unpark A13 Graph
- mkdir a private `#Test_Database` inside the unzip
- Treat DEMO as a LIVE proof

## Proof

```
python -m ate.core.check_cloud_db
python -m ate.core.check_launch
python -m ate.core.check_ui_contract
python pack_ate_console.py --check
```
