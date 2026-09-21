keywords: report-coverage, ocr, ingest-audit, lab-report, vix, vox, autofill, all-families, sheet-map
main_idea: Local Product Testing Report workbooks (all classes) map to existing TestSpecs. Ingest --audit writes coverage.json. Enable cin/cpd/tp where those sheets already exist. Do not invent IOZ/RON/TrTf. Qianfan stays parked.

## Report formats (probed, not guessed)

- opamp_lab: Summary/Checklist + Slew Rate/GBW/VOS/PSRR (RS622, LM358 training).
- logic_lab_vix_vox: VIX + VOX/VOL + ICC + CIN/CPD + tPD (1G07/08/14/32/125).
- logic_split_vih_voh: separate VIH/VIL/VOH/VOL (1G126, RS0204).
- switch_ron: RON/ICC/IOZ (RS2323, RS2227). Only iplus/leakage TestSpecs exist.
- other: Soo I2C (RS29511), GT32D Chinese high-low, 1G97 VTH/IC.
- Instrument datalog xlsx under Files/Raw Data is not the campaign lab book.

## Autofill path (already in ate/)

1. Import xlsx -> workbook/ (source stays golden).
2. campaign_outline probes VOX/ICC/VIX sheet_map (no A91).
3. Tests page Save this Version -> test_catalog.yaml.
4. Results Fill Excel numbers -> *_filled.xlsx.
5. ingest_datasheet: PDF text -> limits yaml -> copilot unmapped ids. OCR only if thin. Cloud HTML one SKU if still thin. Paddle autodownload last. Qianfan parked.

## Enabled existing codes from sheets

cin/cpd (and tp where tPD exists) on 1G07/08/14/32/97/125/126/GT32D. G97 also delta/II. Do not enable slew on Logic leftover SR/PSRR pages.

## Still no TestSpec (do not Path B this turn)

IOZ, RON, Ton/Toff, TrTf, ISC, Soo UVLO/TPRE/BACKFLOW, RS0204 Ioz/Timing extras.

## OCR

Fat local PDF text already extracted for most SKUs. Thin/missing PDF: AUP1G07, RS164, RS29511, GT32D. Next ingest: `python -m ate.core.ingest_datasheet --audit` then one SKU `... RS1G07 --no-web`.

Proof: python -m ate.core.check_report_coverage ; check_ingest_datasheet ; check_add_test
