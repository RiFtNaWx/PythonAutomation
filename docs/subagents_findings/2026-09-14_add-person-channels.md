---
keywords: add-person, chuntat, operator-dropdown, probe-channels, walk-order, plus, later, continue
main_idea: Type a new operator name, Add person confirm popup creates folders and fills the top dropdown. Probe channels scale with + / x; walk-order text follows the ticked letters.
---

PREFLIGHT: PARTIAL. Reuse: 2026-09-14_a22-assign-skus-shipped, 2026-09-14_run-continue-later. Spawn: skip.

## Operator Add

Labels **Add** is Kind/Value, not a person. Daily Setup now has **Add person**. Unknown Operator folder + Apply also opens `#add-operator-modal`. Create folders calls `assign_owner_products` for the **current Setup Part** (not More-panel SKU chips), then Apply, then `#owner-select` includes that name.

Live 2026-09-14: typed Chuntat, popup title `Add Chuntat?`, Create folders -> top dropdown `chuntat`, campaign `OpAmp / RS622 / TTSOP8 / Chuntat / Version_1`, notice `Added Chuntat`. First click also cloned Eugene's SKU chips (4 folders); JS now uses Setup Part only.

## Channels

`normalize_probe_channels` accepts CHA..CHH. UI chips: tick, `+` next letter, `x` remove (keep one). Untick B -> walk `Channel first (A all DUTs)`. `+` keeps B off and adds C; walk `A then C`.

## Continue (same run)

WAIT / DELAY / RUN strip, Later parks Continue, header Waiting reopens. START never auto-continues.

## Check

```
python -m ate.core.check_ui_contract
python -m ate.core.check_walk_order
python -m ate.core.check_assign_owner
```

Ctrl+F5 (`?v=20260914opch3`). Worker restart after runner/specs (already done).
