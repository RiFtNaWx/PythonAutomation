---
keywords: onedrive, shortcut, sync, cloud_db, #Test_Database, RS-Train, sharepoint, drag-copy
main_idea: This PC's #Test_Database is a local drag-copy at C:\Users\OoiJianHong\#Test_Database (not OneDrive). Sync fails because OneDrive already has a shortcut into the same RD Shared Documents library (RS-Train). ATE already writes here.
---

# 2026-09-14 Local #Test_Database vs OneDrive shortcut

PREFLIGHT: HIT on 2026-09-11_app-vs-dev-cloud-db + CLOUD_TEST_DATABASE.md. Spawn: skip.

## What is on this PC

- Path: `C:\Users\OoiJianHong\#Test_Database` (Explorer: Oo Jian Hong > #Test_Database). Not a symlink. No cloud attributes.
- After Replace: shortcut is `C:\Users\OoiJianHong\OneDrive - JumpWin Tech\Research & Development - #Test_Database`. Robocopy 633 newer files from the local drag-copy into it (Logic 286 json, newest RS74AUP1G07 09:57). `cloud_db.txt` and `sync_cloud_db` now point there.
- Everyone URL: SharePoint Handover / Jianhong / #Test_Database. Tutorial images 04 and 06 were Cursor screenshots -- replaced with UACC Explorer + Notepad. Added 09-sharepoint-testdb.png.
- Families present: AnalogSwitch, Level, Logic, OpAmp, Power, `_ate`.
- Live writes today: Logic/RS1G07/SOT23/Eugene/Version_1 sessions at 09:46.

## Why Sync shows the X

OneDrive already mounts RD Shared Documents via shortcut:

`C:\Users\OoiJianHong\OneDrive - JumpWin Tech\=Daily Task 8am\RS-Train`

Remote: `https://jumptechwin.sharepoint.com/sites/RD/Shared Documents/General/Reference Doc/RS-Train-202602`

Microsoft: one shortcut per shared library. `#Test_Database` is also under `sites/RD/Shared Documents/...` so Sync / Add shortcut on it fails with "You're already syncing a shortcut to a folder from this shared library."

## Do / do not

- Keep using the local folder for ATE on this PC. Do not click Sync again.
- Do not save Notepad `cloud_db.txt` with a list bullet in front of the path.
- To share later: remove the RS-Train shortcut (or replace it with a parent shortcut to `General`), then Add shortcut once to `#Test_Database`, then update `cloud_db.txt` to that OneDrive path. Do not do that while RS-Train is still the library shortcut.
