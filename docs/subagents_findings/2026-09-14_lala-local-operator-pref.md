---
keywords: lala, ate_operator, local-preference, add-person, first-run, pic, get_db_context, campaign-by-owner
main_idea: This browser's ate_operator is the person. Add person / first-run lands on that name plus ticked products. Worker last-apply and inventory pic must not steal Eugene.
---

PREFLIGHT: HIT. Reuse: 2026-09-14_first-run-name-multi-sku.md, 2026-09-14_add-person-channels.md, 2026-09-14_chun-wei-click-provision.md, 2026-09-14_add-person-products.md. Spawn: skip.

## Job

Type Lala, Add person. This PC becomes Lala with Lala's products unless they change ticks. Shared OneDrive `#Test_Database` stays. Not a Users table.

## Steal (root cause)

1. `applyOwner` used inventory `pic:` as the folder, so Lala on RS622 became Eugene.
2. `loadDb` preferred worker `get_db_context` (process-global last Apply on :8766) over `ate_operator`.
3. `paintCampaign` called `syncOwnerSelectFromFolder` and overwrote `ate_operator` to the painted campaign (Eugene).
4. Boot ran `loadDb` before `loadOwners`.

## Fix

- `applyOwner`: folder = person label. Restore `ate_last_campaign_by_owner` if present.
- `campaignForThisPc` / `loadDb`: this PC's person wins; skip Apply on first-run.
- `paintCampaign`: do not stamp Eugene into `ate_operator` when this PC is already someone else.
- Boot: `loadOwners` then inventory then `loadDb`.
- Family rail / inventory tree: `writeOperatorLabel()` before `pic`.
- Add person: `saveOwner` + upsert defaults to the kept SKU + Apply as that name.

## Not

`runner.py`, `database.py` path shape, A13, scrape, a private `#Test_Database`.

## Check

```
python -m ate.core.check_ui_contract
```

Ctrl+F5 (`?v=20260914lala1`). Worker restart not required (static UI).
