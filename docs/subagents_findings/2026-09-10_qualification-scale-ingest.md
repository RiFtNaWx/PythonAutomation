---
keywords: qualification, sheet_class, inventory, ensure_product, workbook-ingest, golden-merge, level, logic
main_idea: Re-checked Qualification Main (33 SKUs). All types match. Extras now have sheet_class. Create folders copies the tracking xlsx into #Test_Database/.../workbook/ and applies golden layout only if OpAmp sheets exist.
---

# 2026-09-10 Qualification scale + new-product ingest

PREFLIGHT: PARTIAL. Reuse: sheet-class-classification, product-testing-report, new-product-demo. Spawn: skip.

## Classification (Excel SoT)

Source: `Product Testing Report/Qualification Product List-20260320.xlsx` Main (33 rows).

| sheet_class | category | n |
|---|---|---|
| Logic Series | logic | 18 |
| Linear Regulator | power (stub) | 5 |
| Level Shifters | level (RS0204 ate_suite=logic) | 4 |
| Low Noise Op-Amp | opamp | 3 |
| Analog Switch | analog_switch | 1 |
| General Op-Amp | opamp | 1 |
| Precision Op-Amp | opamp | 1 |

Zero Main SKUs missing from inventory. No misclass vs Main.

Extras (not on Main), now labeled:

- LM358 -> General Op-Amp / opamp
- RS2227 -> Analog Switch / analog_switch
- RS29511 -> Logic Series / logic
- RS1GT32D -> Logic Series / logic

RS2323 PTR folder has 0 xlsx -- ingest skips until a workbook lands.

## New product -> exact DB

`ensure_product` still writes `#Test_Database/{Component}/{Part}/{Package}/{Operator}/Version_1`.

If the tracking row has `report:` and the campaign workbook/ is empty, it copies that xlsx (existing `import_workbook`). Golden merge runs only when the file has OpAmp `TEST_SHEETS`. Logic/LIM reports stay as copied. DEMO still does not stamp PASS. Result paste stays `session_paste` + sheet_map cells (FILL_ME until measured).

Check: `python -m ate.core.check_new_product`
