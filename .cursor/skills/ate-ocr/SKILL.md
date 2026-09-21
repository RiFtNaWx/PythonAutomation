---
name: ate-ocr
description: >-
  Routes datasheet PDF text and OCR for ATE limits and golden Excel fill. Use
  when the user says OCR, PaddleOCR, EasyOCR, Qianfan-OCR, Unlimited-OCR, upload
  datasheet, fetch English limits, min max, sweep Excel, *_filled.xlsx, or
  Fill Excel. Pipeline: text first, cloud one-SKU HTML if thin, autodownload
  Paddle/Easy only if still thin, write limits yaml, probe live xlsx cells,
  fill golden copy not the source xlsx. Never dump into #Test_Database.
  Do not paste a Copilot block; agents already have AGENTS.md / CLAUDE.md / AI.md.
---

# ATE datasheet ingest (OCR only if needed)

Run: `python -m ate.core.ingest_datasheet RS0204 --pdf "C:\path\RS0204.pdf" --xlsx "C:\path\report.xlsx" --no-web`

Recipe (later AI): `docs/datasheet/INGEST.md`. Specs SoT `ate/config/limits/<key>.yaml`. Truth table SoT `ate/config/parts/<key>.yaml`. Export `ate/config/datasheets/tables/<key>.json`. Paths: `ate.core.paths.PATH_RULE` (slice at `#Test_Database`, store `%USERPROFILE%` or relative `report:` keys). Never commit `C:\Users\<name>` into `coverage.json`.

Proof: `python -m ate.core.check_ingest_datasheet`.

## Route (stop at first rung)

1. Local PDF text (`lookup._pdf_plain`). Fat text = no OCR.
2. Cloud HTML for **this SKU only** (`datasheet.fetch_and_store`) if text is thin.
3. Autodownload [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) then [EasyOCR](https://github.com/JaidedAI/EasyOCR) only if still thin.
4. [Qianfan-OCR](https://huggingface.co/baidu/Qianfan-OCR) / [Unlimited-OCR](https://github.com/baidu/Unlimited-OCR) stay parked (5B / long-horizon). Do not autodownload those.

## Then (compulsory)

1. Merge `ate/config/limits/<key>.yaml` (do not overwrite filled min/max / rs622 hand-kept).
2. Map `sheet_map` `paste.values` ids -> sheet!cell. Do not guess A91. Probe the uploaded xlsx.
3. Copy golden xlsx -> `*_filled.xlsx` (SIM `*_demo.xlsx`). Source stays clean.
4. Sweep `data.rows` -> sorted `Sweep` sheet + `sessions/sweep_summary.md` (VCC then freq then AWG).
5. Agents already read `AGENTS.md` / `CLAUDE.md` / `AI.md`. Do not ask the operator to paste a prompt.

Upload a PDF: `python -m ate.core.ingest_datasheet RS0204 --pdf "C:\path\file.pdf" --xlsx "C:\path\file.xlsx"` copies the PDF into local Reference as `{PART}_(RevUpload).pdf`, never into `#Test_Database`. RS0204 is Level + `ate_suite: logic` (LOGIC fixture), not OpAmp BUFFER.
