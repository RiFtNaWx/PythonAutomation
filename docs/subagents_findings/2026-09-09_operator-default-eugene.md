---
keywords: unassigned, eugene, bench.yaml, prefer_live_operator, stub-family, demo-timeline, map-coverage, a15, a17
main_idea: Default campaign now lands on Eugene/Version_1 (not empty _unassigned). Stub RUN-IC classes clear the registry. DEMO paints the Run timeline. Map coverage no longer says OK when n_map is 0.
---

# 2026-09-09 Operator default + ticket close

PREFLIGHT: PARTIAL. Reuse: 2026-09-08_operator-flow-e2e-review, f22, a17. Spawn: skip.

## Root cause

`bench.yaml` still pointed at the 4-level `TTSOP8/Version_1` path. `default_context` treated that as operator `_unassigned`, so lab-report and mapped-tests checks looked at an empty leftover tree while the live workbook is `TTSOP8/Eugene/Version_1`.

## Fixes

- `prefer_live_operator` skips `_unassigned` when a person folder has the version
- `load_family("")` clears tests for Power/Comparator stubs
- UI picker skips `_unassigned`; DEMO paints timeline; map coverage empty != OK
- Detect reads `utf-8-sig` so BOM files parse

## Checks (this turn)

Green: new_product, operator_tree, ui_contract, family_load, open_inventory, test_detect, tags_datalog, lab_report_sync, mapped_tests, logic_campaign, psu_protect, photo_layout.

`check_golden_workbook` fail-closed on Eugene xlsx (GBW/Settling screenshots on disk, not embedded). That is campaign data, not a missing feature. Fix path: session-end paste or `--fix`. Do not unpark A13/A14.

## UI

Worker idle-restarted. Console at :5174: OpAmp/Eugene, Logic/Ariff, START disabled, DEMO 17/17, Results sheet_map grid, Tags save controls. Ctrl+F5 (`app.js?v=20260909goal`).
