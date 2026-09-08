# ATE agent guide (PythonAutomation)

Read this before editing the operator console or adding a product family.

## Where things live

| Task | Place |
|------|--------|
| Add a test / family | `docs/ATE_PLUGIN.md` + `ate/tests/<family>/` `register(TestSpec)` |
| Campaign folders | `#Test_Database/{Component}/{Part}/{Package}/{Operator}/{Version_N}/` via `ate/core/database.py` |
| Tags (board / project) | `_manifest/tags.yaml` + campaign-root `TAGS.txt` (`ate/core/tags.py`) |
| Session run record | `sessions/session_*.json` (per START) |
| Rolling STS datalog | `sessions/report.json` + `sessions/archive/` (`ate/core/datalog.py`) |
| Photo boxes in Excel | `_manifest/sheet_map.yaml` `tests.<key>.paste.photos` (`ate/reporting/photo_layout.py`) |
| Paste into workbook | `ate/reporting/lab_report.py` + `ate/reporting/session_paste.py` |
| Golden layout | `ate/reporting/golden_layout.py` + `check_golden_workbook` |
| Operator UI | `ate/ui/web/` -- follow `ate/ui/web/UI_CONTRACT.md` |

## Ports

- Worker JSON-RPC: **8766** (`ate.worker.server`)
- UI: **5174**
- Do not use 8765 (AirGPT) or founder-reserved 3000/3001/5000

## After code that the worker loads

Idle-restart with `restart_ate_worker.bat`. Static UI: tell operator **Ctrl+F5**.

## Do not

- Add a Tags folder axis under `#Test_Database`
- Hardcode A91 photo cells in Python (use sheet_map)
- Invent a second Excel writer / unpark A13 OneDrive MCP here
- Touch A16 detect/wrap UI when working A17 tags
