# EPIC-A17 - Tags, session datalog JSON, auto-paste, golden workbook

**PRD:** PRD-001 F24
**Status:** implemented (F24)
**Do not reopen:** A01-A16. A13 Excel merge-center / OneDrive and A14 xyflow stay parked.
**Branch:** `epic/a17-tags-session-datalog`

## Goal

1. Campaign tags in `_manifest/tags.yaml` + grep-able `TAGS.txt` (no new folder axis).
2. Rolling STS-shaped `sessions/report.json` + timestamped `sessions/archive/`.
3. Tags page + chips beside model; `AGENTS.md` + UI contract check.
4. Auto-paste screenshots into `sheet_map` `paste.photos` cells; campaign golden layout check/fix.

## Tickets

| ID | Seam |
|----|------|
| A17-T01 | tags + datalog + boards.yaml + RPCs + `check_tags_datalog` (no UI) |
| A17-T02 | Tags tab + chips + AGENTS.md + UI_CONTRACT.md + `check_ui_contract` |
| A17-T03 | session-end auto-paste + `apply_golden_workbook` + `check_golden_workbook` |

## Parked (not this epic)

- A13 OneDrive / Excel MCP merge-center
- ML / predictive-maintenance trainer
- Windows NTFS Keywords
- Encoding tags into screenshot filenames
- Reopening A16 detect/wrap UI

## Checks

```
python -m ate.core.check_tags_datalog
python -m ate.core.check_ui_contract
python -m ate.reporting.check_golden_workbook
python -m ate.core.check_family_load
```

## Acceptance

See PRD-001 EPIC-A17 acceptance block (buyer seat).
