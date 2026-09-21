---
keywords: autofill, golden, narrative, photos, slew, datasheet, senior, annotate, filled-xlsx, cha-chb
main_idea: Product Testing Report xlsx (OpAmp golden) is the paste SoT. STS PDF is the research log. Fill Excel writes numbers, datasheet/conclusion text, comments, and merge-sized photos onto *_filled.xlsx. Two photo boxes on a row = CHA|CHB, including 8-col Slew.
---

# 2026-09-14 Autofill vs golden lab report

PREFLIGHT: PARTIAL. Reuse: report-ocr-coverage, adaptive-photo-boxes, campaign-outline, ingest-datasheet-golden-excel. Spawn: skip.

## Claim (efficiency)

1. **Product Testing Report xlsx from a senior** -- most efficient paste target. Same left intro (conditions / circuitry / datasheet / conclusion), DUT number grid, CHA/CHB photo boxes. Probe cells. Do not invent a third format.
2. **ATE Fill Excel (`*_filled.xlsx`)** -- writes onto a copy of that book. Numbers in `paste.values`, intro in `paste.narrative`, photos in discovered merges. Source golden stays clean.
3. **STS datalog PDF** -- research / P/F history. Not a lab-book replacement.

AI agent job: annotate paste cells from the OpAmp golden (Slew Rate CHA left, CHB right; DUT #1-#4 tables). Do not copy OpAmp `layout_rules` onto Logic.

## What was stupid before

- Fill only wrote numbers. Datasheet/Circuitry stayed `#VALUE!`.
- Photo discover assumed 4-col DUT grid, so 8-col CHA|CHB Slew boxes were missed or tagged as DUT2.
- Photos used a 420x240 cap instead of the merge box.
- No cell comments saying what belongs where.

## Build

- `golden_layout.discover_photo_anchors`: 4-col DUT grid or 8-col pair; two boxes on a row = u1 CHA/CHB.
- `campaign_outline.attach_known_narrative`: probe intro B cells.
- `session_values.fill_workbook_from_report`: crawl limits yaml + fixture checklist; conclusion = measured vs min/max; comments; photos on the copy.
- Setup / Results hint: get the xlsx from a senior or an AI agent.

Proof: `python -m ate.core.check_session_values` ; `python -m ate.reporting.check_photo_layout` ; `python -m ate.core.check_campaign_outline` ; `python -m ate.core.check_ui_contract`
