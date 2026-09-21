---
keywords: [a19, a20, join-all, vox, sop8, golden-skip, merged-cell, rs1g08, rs2323]
main_idea: PDF glyph-join recovers VOH tables. Logic fill uses tracking VOX G16 not empty VOH sheets. Do not golden-merge a filled tracking xlsx.
---

# 2026-09-11 Join-all extract + Logic/LIM DUT fill

PREFLIGHT: PARTIAL. Reuse: 2026-09-11_a19-a20-a21-handover.md, 2026-09-11_voh-icc-excel-match.md, 2026-09-11_family-pdf-class.md. Spawn: skip.

## A20

`_pdf_plain` concatenates TJ/Tj glyphs then collapses whitespace. Space-joining shredded `VOH` into `V O H`. RS1G08 extract now contains `IOH = -32mA 4.5V 3.8`. Do not parse 1.65V corners into `voh_table` (platform stays 2.0/3.3/4.5/5.0/5.5). RS2323 8.4 TOC + banner `ON-State Resistance, 0.6` are text; rON min/max table body is still not in the extract (image). ICC banner max 1 uA is +25C; Full max 10 stays unused.

## A19

Tracking Logic reports use sheet **VOX** (G/H/I = DUT 1-3) and **ICC** D10 = max, not campaign stub VOH/VOL. Map only the overlapping 4.5V corner (`VOH_4p5V` G16, `VOL_4p5V` G25) plus `ICC_uA` D10. Do not dump a single DEMO ICC onto RS0204 Icc C27 (condition grid). RS2323 Iplus stub is labeled `ATE IPLUS_uA` at B2.

SOP8 ingest ran OpAmp golden merge-center over GBW `B18:L30`, turning C21 into MergedCell. Skip golden when GBW/VOS already have numbers. Fill skips MergedCell instead of crashing session end.

## Proof

```
python -m ate.core.check_lookup
python -m ate.core.check_session_values
python -m ate.core.check_specs_datalog
python -m ate.core.check_new_product
```

DEMO fill: RS1G08 VOX!G16=3.8, ICC!D10=1; RS2323 Iplus!B2=1; RS622 SOP8 GBW!C21=7, VOS!B16=0.7; RS0204 STS ICC/IL/VOH/VOL PASS (no Icc grid map).
