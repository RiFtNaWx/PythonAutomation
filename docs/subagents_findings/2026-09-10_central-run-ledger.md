---
keywords: run-ledger, central-db, sharepoint, onedrive, list_runs, delete-session, labels-clear, test_database_root
main_idea: #Test_Database is the shared database. SharePoint means sync that folder. Results Run ledger lists session JSON for every operator; Delete removes JSON only. A13 Graph/MCP stays parked.
---

# 2026-09-10 Central DB + run ledger

PREFLIGHT: PARTIAL. Reuse: 2026-09-08_a17-tags-session-datalog, 2026-09-09_product-testing-report-inventory, parked A13. Spawn: skip.

## What the lab asked

Edit/delete/improve labels. Trace who ran what. One central place for runs, reports, and software data. Cloud/SharePoint.

## What we built (existing tree, no second stack)

- `bench.yaml` `test_database_root` is the central folder. Sync it with OneDrive/SharePoint if the lab wants the same tree in the cloud.
- Results **Run ledger**: This campaign / This SKU (all operators) / All campaigns. Open / Apply / Delete.
- Delete = one `sessions/*.json` or `sessions/archive/*.json`. Never workbook or Version folders.
- Tags **Clear all tags**. Chip x still removes one.
- Setup **Open central DB** + path hint (`cloud_kind` local|onedrive|sharepoint from the path name).

## Parked (do not unpark)

- A13 OneDrive / Excel MCP / Graph API
- A second Excel writer
- Tags as a `#Test_Database` folder axis

## Checks

```
python -m ate.core.check_ui_contract
python -m ate.core.check_tags_datalog
python -m ate.core.check_new_product
```

UI `?v=20260910ledger1`. Worker 0.2.20. Ctrl+F5.
