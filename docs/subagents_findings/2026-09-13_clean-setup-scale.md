---
keywords: [setup-clean, scale, apply-campaign, open-sim, start, all-gate, rs1g08, operator-folders]
main_idea: Daily Setup is five campaign combos + Apply + Session + START. Person/tags/import stay in More. Live 5174 proved Logic RS1G08 Ariff Version tree, All is view-only, Open SIM enables START.
---

# 2026-09-13 Clean Setup + scale on live UI

PREFLIGHT: PARTIAL. Reuse: 2026-09-13_prd-clean-run-ux, 2026-09-11_scale-operator-tree, 2026-09-10_ux-scale-fixes. Spawn: skip.

## Shipped

1. Daily Test Database row is Component / Part / Package / Operator / Version. Person Save/Forget, tags, year, model, import, new product stay in collapsed `details.setup-more`.
2. START / DEMO sit next to Select all (above the accordion), not below it. `.btn.big` in that row is auto-width so START is not a full-width grey bar.
3. OpAmp board gains start collapsed. Logic hides the panel.
4. Local `ate/config/cloud_db.txt` points at `C:\Users\OoiJianHong\#Test_Database` (gitignored). App launched via `ate.ui.launch` on 8766 / 5174.

## Live scale (browser 5174)

| Claim | Result |
|-------|--------|
| Family Logic fills RS1G08 / SOT23 / Ariff | PASS |
| Operator list is many people, not a Users table | PASS (Ariff, Soo, Eugene, ChangThong, ...) |
| Header All + Apply refuses write | PASS alert `Pick a person (not All / Kevin observer)` even when folder is Ariff |
| Header Ariff picks latest Version_N | PASS Version_2 |
| Open SIM enables START | PASS tiles MSO/PSU/AWG/DMM on; SIM::* resources |
| Combo change does not wipe another person's folder | PASS (All-gate + folder still Ariff) |

## Checks

```
python -m ate.core.check_ui_contract
python -m ate.core.check_launch
python -m ate.core.check_cloud_db
python -m ate.core.check_operator_tree
```

All exit 0. UI cache `?v=20260913ux5`. Ctrl+F5.

## Not this pass

- Map coverage FAIL `Supply_Current->ICC, VOH->VOX, VOL->VOX` on Ariff RS1G08 (A19 leftover).
- Hardware USB Open Session. SIM only.
- Full DEMO/START of the Logic suite (would sit on Continue gates).
