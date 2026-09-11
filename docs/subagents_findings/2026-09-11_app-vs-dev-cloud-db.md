---
keywords: cloud-db, sharepoint, app-zip, vibe-code, cloud_db.txt, ATE_APP_ONLY
main_idea: Operators get START.bat zip against one SharePoint-synced #Test_Database. Vibe-coders clone git. https URL in sharepoint.url; local OneDrive path in cloud_db.txt. No private unzip DB. A13 stays parked.
---

# 2026-09-11 App zip vs git + central SharePoint DB

PREFLIGHT: HIT on 2026-09-10_central-run-ledger + 2026-09-11_ate-try-packet. Spawn: skip.

## Split

- App: `pack_ate_console.py` zip, `START.bat`, `ATE_APP_ONLY=1`, refuses to mkdir a private `#Test_Database`.
- Dev: git clone + AGENTS.md. Same `test_database_root`.

## Path order

`ATE_TEST_DATABASE_ROOT` env -> `ate/config/cloud_db.txt` -> `bench.yaml` `test_database_root`.

https link: `ATE_SHAREPOINT_URL` / `ate/config/sharepoint.url` / bench `sharepoint_url`. Open central DB opens the folder if present, else the https. Does not mkdir.

## When Jian Hong pastes the SharePoint link

1. Save it as `ate/config/sharepoint.url` (one https line).
2. Rebuild zip.
3. Each person: Add shortcut / sync library in OneDrive, paste *that local folder* into `cloud_db.txt`.

Windows cannot use the https URL as a filesystem. That is why two files.

## Proof

```
python -m ate.core.check_cloud_db
python -m ate.core.check_ui_contract
python pack_ate_console.py --check
```
