---
keywords: [a19, vox, 1.65, 2.3, 3.0, voh-table, rs1g08, rs1g32]
main_idea: Probe every unique VOX Vcc row (not only 4.5V). Tracking 1.65/2.3/3.0 corners go into voh/vol tables and limits. Do not alias 1.65 as VOH_2p0V.
---

PREFLIGHT: PARTIAL
reuse: docs/subagents_findings/2026-09-11_vox-probe.md, 2026-09-11_campaign-outline.md
spawn: skip

# 2026-09-11 VOX all sheet Vccs

RS1G08 VOX DUT rows: 1.65 G12, 2.3 G13, 3.0 G14, 4.5 G16 (VOL 1.65 G21 ... 4.5 G25).
RS1G32 shifted: 1.65 G17, 4.5 G21.

`campaign_outline._probe_vox_corners` maps each unique column-A Vcc. Duplicate 3.0 (IOH -16 vs -24) keeps the first row.

Part yaml `voh_table` / `vol_table` on rs1g08 / rs1g32 / rs1gt08 / rs1gt32 / rs1gt32d gained tracking corners from the sheet Spec column. Yaml 2.0/3.3/5.0/5.5 stay for START; they have no VOX cells.

Proof:

```
python -m ate.core.campaign_outline --apply
python -m ate.core.check_campaign_outline
python -m ate.core.check_specs_datalog
python -m ate.core.check_lookup
```
