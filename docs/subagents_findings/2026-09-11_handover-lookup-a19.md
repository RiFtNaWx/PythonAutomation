---
keywords: [handover, lookup, datasheets, a19, a20, a21, paste-values, reference-pdf]
main_idea: Local Reference PDFs are the datasheet SoT (datasheets.yaml + limits yaml). Excel numbers fill from paste.values. Setup combos require Apply. Web scrape only if PDF missing.
---

# Handover lookup + A19/A20/A21 (2026-09-11)

Local PDFs: `C:\Users\OoiJianHong\Downloads\Reference\Reference`. Index `ate/config/datasheets.yaml`. Extract text under `ate/config/datasheets/text/`.

Do not scrape en.run-ic.com into `#Test_Database`. Fetch website only when `resolve_pdf` misses.

A19: `session_values.fill_workbook_from_report` + RS622 GBW `R20`.
A21: combo change no longer auto-applyDb.
