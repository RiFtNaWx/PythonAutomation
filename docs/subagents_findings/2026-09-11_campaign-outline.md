---
keywords: [campaign-outline, rs622, sheet-map, fill-me, vox, scale, a19]
main_idea: One RS622-shaped campaign_outline writes every sheet_map. No FILL_ME. Known paste cells (VOX/ICC/Iplus/GBW/VOS) live in that module so per-Version edits stop.
---

# 2026-09-11 Campaign outline (RS622 format at scale)

PREFLIGHT: PARTIAL. Reuse: 2026-09-11_joinall-vox-fill.md, 2026-09-11_voh-icc-excel-match.md. Spawn: skip.

`ate/core/campaign_outline.py` is the single outline: `folder`, `excel_sheet`, `fixture_mode`, `automated`, `dut_iterations`, `sample_size`, `naming`, `workbook.path`. Import and `ensure_product` call it. `python -m ate.core.campaign_outline --apply` upgrades live `#Test_Database` maps. `python -m ate.core.check_campaign_outline` fails on missing `fixture_mode` and leftover FILL_ME.

Do not copy OpAmp `layout_rules` onto Logic. Do not invent photo cells (TTSOP8 8-box photos only when GBW R20 is writable). RS0204 `Icc` stays unmapped. Tracking VOX G16 / ICC D10 / Iplus B2 / GBW R20 or C21 stay the only auto numeric cells.
