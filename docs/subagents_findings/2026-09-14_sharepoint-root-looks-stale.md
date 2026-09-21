---
keywords: sharepoint, onedrive, sync, #Test_Database, cloud_db, handover, stale, RS1G07
main_idea: ATE already writes the real OneDrive shortcut of Handover/Jianhong/#Test_Database. SharePoint root still shows the same 5 folders from 11 Sep so it looks frozen; today's files are under Logic/RS1G07. Dead copy at C:\Users\OoiJianHong\#Test_Database is not the cloud.
---

# 2026-09-14 SharePoint root looks 3 days old

PREFLIGHT: HIT on 2026-09-14_local-testdb-onedrive-shortcut + CLOUD_TEST_DATABASE.md. Spawn: skip.

## What is true on this PC (14 Sep 11:20)

- Worker 0.2.38 `test_database_root` = `C:\Users\OoiJianHong\OneDrive - JumpWin Tech\Research & Development - #Test_Database`
- OneDrive SyncEngine `FullRemotePath` = `https://jumptechwin.sharepoint.com/sites/RD/Shared Documents/General/Handover/Jianhong/#Test_Database` (same URL as `sharepoint.url`)
- Newest writes: `Logic/RS1G07/SC70-5/Eugene/Version_1/sessions/` at 11:20 (xlsx, datalog.pdf, session json)
- Dead local copy `C:\Users\OoiJianHong\#Test_Database` last write 09:57 (RS74AUP1G07). Do not use it.
- Mount `LastModifiedTime` 2026-09-14T02:03:11Z (~10:03 SGT) = shortcut add / first index, not proof that 11:20 files are already on the website

## Why the website looks unchanged

The AllItems view of `#Test_Database` still lists AnalogSwitch / Level / Logic / OpAmp / Power. Those names were created ~11 Sep. New work is inside `Logic/`, not a new top folder.

If Logic > RS1G07 > SC70-5 > Eugene is missing on the website, OneDrive has not finished (or is paused). Check Explorer Status on the OneDrive shortcut (cloud arrows), not the home `#Test_Database` folder.

## Do not

- Unpark A13 Graph
- Point `cloud_db.txt` back at `C:\Users\OoiJianHong\#Test_Database`
- Click SharePoint Sync again
