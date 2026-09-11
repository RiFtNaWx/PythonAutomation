---
keywords: sharepoint, rd-handover, rs622-golden, photo-boxes, eugene-branch, pass-fail, datasheet-guide
main_idea: RD SharePoint #Test_Database is the cloud tree (same AnalogSwitch/Level/Logic/OpAmp/Power). Eugene TTSOP golden xlsx drives 8 photo boxes per sheet (ORT 16). Missing Slew/NPR/PowerOn/VOL maps filled. App zip vs git unchanged. Push eugene-console when checks pass.
---

# 2026-09-11 SharePoint RD #Test_Database + RS622 photo boxes

PREFLIGHT: HIT on central-run-ledger, app-vs-dev-cloud-db, a19 handover, joinall-vox-fill. Spawn: skip Graph/A13.

## SharePoint

Sharing link (saved `ate/config/sharepoint.url` + bench `sharepoint_url`):
https://jumptechwin.sharepoint.com/:f:/s/RD/IgC_gG1VFnI3RbuN7gqBaNAxAU6m3sLDVuj4EIdauFRGG4E?e=te8KJN

Chrome title: Research & Development / Documents / #Test_Database.
Folders: AnalogSwitch, Level, Logic, OpAmp, Power (same as local `C:\\Users\\OoiJianHong\\#Test_Database`).
Do not treat the https URL as a filesystem. OneDrive sync / Add shortcut. A13 parked.

## Golden Excel

`...\\Eugene\\Version_1\\workbook\\RS622XK_Lab_Report_TTSOP.xlsx`
Photo SoT from `_manifest/golden_layout_report.json` (do not re-apply golden insert on a filled book).

Each non-ORT sheet: 8 boxes (DUT1-4 x CHA/CHB). ORT: 16 (POS/NEG).
Filled missing maps: SlewRate A70, NoPhaseReversal A41, PowerOnTime A59, VOL A42.

## Datasheet / P/F

Run checkboxes show min/max/typ from `limits/<part>.yaml` or "datasheet unspec -- Fetch limits".
STS export still stamps pass/fail when min/max exist. SR typ 3.7 V/us from RS62X banner; SR min/max still missing from table extract.

## Proof

```
python -m ate.core.check_campaign_outline
python -m ate.core.check_ui_contract
python -m ate.core.check_cloud_db
```
