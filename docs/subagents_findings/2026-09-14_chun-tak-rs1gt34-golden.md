---
keywords: chun-tak, chuntat, rs1gt34, lab-report, golden, ingest, run-ic, ocr, vix, vox, ioff, cin, cpd
main_idea: Typo Chuntat -> Chun Tak. RS1GT34_Lab_Report.xlsx is that person's golden (VIX/VOX/ICC/IOFF/CPD/CIN/tPD). RUN-IC fetch for SKUs with no local PDF; restore Downloads Reference from #Test_Database/Reference if that folder is emptied.
---

# 2026-09-14 Chun Tak + RS1GT34 golden ingest

PREFLIGHT: PARTIAL. Reuse: rs1gt34-vih-voh-sweep, ingest-datasheet-golden-excel, gt08-gt32-ariff-report-drop, report-ocr-coverage. Spawn: skip.

## What shipped

1. Operator `Chuntat` -> id `chuntak` / label `Chun Tak` (xlsx Summary K3). Folders renamed. Default Logic / RS1GT34 / SOT-353.
2. Golden: `Downloads/RS1GT34_Lab_Report.xlsx` copied to Product Testing Report drop and `#Test_Database/Logic/RS1GT34/SOT-353/Chun Tak/Version_1/workbook/`. Source not overwritten. Filled copy is `*_filled.xlsx`.
3. Tests from sheets (not ten/tdis): `vih_vil`, `voh_load`, `vol_load`, `supply_current_sweep`, `ioff_leakage`, `cpd`, `cin`, `tp`. VCC lists from VIX/ICC/IOFF grids.
4. Limits: CIN 6 pF, CPD 25 pF, IOFF 1 uA from local PDF 9.2/9.3. Do not copy VIX C-column specs (template still says RS1G08; PDF 9.1 table is empty in the extract).
5. Paste probe: ICC `D10` (banner `maximum (uA)`, not conclusion prose), IOFF `D16`, CIN `G19` average, CPD `D12`, VOX G:I DUT columns.

## RUN-IC (one SKU, not catalog)

Fetched into local Reference only:

- RS164, RS3235, RS2227, RS29511 -- English PDF + text (not thin, no OCR).
- RS74AUP1G07 -- no English product page.
- RS1GT32D -- search hits are other details pages; no GT32D PDF. Do not alias RS1GT32XC5.

## Datasheet folder scare

Mid-fetch, `Downloads/Reference/Reference` contained only the four RevWeb PDFs. Original RevA files were restored from `#Test_Database/Reference` (29 pdfs). Index rebuilt (33 pdfs). Cause of the empty Downloads folder is unknown -- fetch_and_store only writes `{SKU}_(RevWeb).pdf` / unlinks that dest. Do not treat Test_Database/Reference as the live lookup root (`bench.yaml` `reference_root` stays Downloads).

## Proof

```
python -m ate.core.check_add_test
python -m ate.core.check_ingest_datasheet
python -m ate.core.check_lookup
python -m ate.core.check_golden_refs
python -m ate.core.check_session_values
```

`check_campaign_outline` still fails three leftover JianHong empty `tests:` maps (RS0302, RS622 SOP8/TSSOP8). Unrelated to Chun Tak.

USB proof: pick Chun Tak, RS1GT34, DEMO `vih_vil` then `voh_load`. Ctrl+F5.
