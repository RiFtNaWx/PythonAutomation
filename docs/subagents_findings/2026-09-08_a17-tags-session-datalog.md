---
keywords: a17, f24, tags, TAGS.txt, datalog, report.json, session-paste, golden-workbook, ui-contract
main_idea: A17 adds campaign tags (yaml+TAGS.txt), STS rolling report.json/archive, Tags page, auto-paste into sheet_map cells, and campaign golden check -- on branch epic/a17-tags-session-datalog.
---

# F24 / EPIC-A17 implement finding

## Shipped

- `ate/core/tags.py` + `ate/config/boards.yaml` + TAGS.txt
- `ate/core/datalog.py` (sessions/report.json + archive)
- Worker RPCs: list/save/import tags, list_boards, filter_campaigns_by_tag, get_session_report, paste/apply/check golden
- Tags tab + chips beside model; `AGENTS.md` + `UI_CONTRACT.md`
- `ate/reporting/session_paste.py` + `golden_workbook.py` + checks

## Checks run

```
python -m ate.core.check_tags_datalog   # OK
python -m ate.core.check_ui_contract    # OK tabs=setup,run,results,tags
python -m ate.reporting.check_golden_workbook  # OK import-only (no xlsx on default ctx)
python -m ate.core.check_family_load    # OK
python -m ate.reporting.check_photo_layout  # OK
```

## Parked

- A13 OneDrive / Excel MCP
- ML trainer
- NTFS Keywords
- A16 UI left alone on this branch

## Operator

Ctrl+F5 `?v=20260908f24`. Tags page after Apply campaign. Grep `TAGS.txt`. Session summary `sessions/report.json`.
