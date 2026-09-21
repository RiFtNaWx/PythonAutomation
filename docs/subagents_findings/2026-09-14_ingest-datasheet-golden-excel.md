---
keywords: [ingest-datasheet, ocr, paddleocr, golden-excel, filled-xlsx, sweep-summary, copilot, limits]
main_idea: Datasheet ingest is text then one-SKU cloud HTML then Paddle autodownload only if thin. Limits yaml plus golden *_filled.xlsx (source untouched). Sweep data.rows sorted onto a Sweep sheet and sweep_summary.md. Copilot prompt lists unmapped Excel cells.
---

# 2026-09-14 Datasheet ingest + golden Excel + sweep

PREFLIGHT: HIT. Reuse: lookup.py, datasheet.py, session_values, campaign-outline, A19/A20 handover, ate-prompt skills.

## Shipped

1. `ate/core/ocr_engine.py` -- OCR only if text < 200 chars. Qianfan/Unlimited refuse.
2. `ate/core/ingest_datasheet.py` -- extract, limits, excel_map, golden fill, sweep sort, copilot block.
3. START/DEMO/Fill Excel copy golden -> `*_filled.xlsx` (SIM still `*_demo.xlsx`).
4. `record_step` keeps `data.rows` so sweeps survive into `report.json`.
5. Results Fetch datasheet RPC calls ingest. Ctrl+F5 for UI.

## Proof

```
python -m ate.core.check_ingest_datasheet
python -m ate.core.check_session_values
python -m ate.core.check_lookup
python -m ate.core.check_ui_contract
```

Does not prove Paddle wheels on a laptop that never needed OCR (RS1G07 PDF has text).

## Not done

Photos still paste into the live xlsx on USB START. Unmapped Logic VOH cells still need a probed sheet_map, not a guessed A91.
