---
keywords: stalker, progress-board, idle, pic, unowned, pickup, board_claim, register-sku, jane, inventory-pic
main_idea: Results Who's working board lists last START per person, idle, tracking PIC vs unowned packages. Pick up / Create calls board_claim (Version_1 + empty pic only, no steal, no scrape).
---

PREFLIGHT: PARTIAL
reuse: 2026-09-11_first-run-progress-board.md, 2026-09-14_a22-assign-skus-shipped.md
spawn: skip

# 2026-09-15 Who's working + unowned pickup

## Shipped

- Results `#panel-progress-board` open by default. People: last product, last run, idle, seen.
- `#progress-owned` = inventory PIC + owners.yaml assigned.
- `#progress-unowned` = empty PIC (PASS rows hidden). Pick up -> `board_claim`.
- Register row creates person + tracking SKU + Version_1. All/Kevin refused.
- Empty PIC only. Existing eugene PIC on RS622 SOP8 is not stolen.
- No new tab. No Users table.

## Proof

```
python -m ate.core.check_progress
python -m ate.core.check_ui_contract
```

Worker idle-restarted. Ctrl+F5 `?v=20260915stalk1`.

## Not

Login. Tags/Users folder. Scraping en.run-ic.com. Stealing another PIC.
