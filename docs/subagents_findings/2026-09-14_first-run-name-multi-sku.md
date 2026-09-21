<!-- keywords: first-run, add-your-name, multi-sku, deselect, chips, combo, startup, absorb, lala, filter, rs622, msop, detect -->
<!-- main_idea: Type Lala then + Add Lala keeps the name (do not wipe). Class/package filters + type RS622 lists tracking SOP8 and TSSOP8 only. Detect compares inventory vs disk; do not invent MSOP8. -->

# First-run absorb name + product filters (2026-09-14)

## Why Lala vanished

`enterFirstRunAddName()` used to set `who.value = ""` when you clicked `+ Add Your Name`. The field was also readonly until Add. Type-then-Add destroyed the text.

Fix: unknown typed text is absorbed (`who.value = pick`). Typing an unknown name sets `data-add-name` without a click. Continue upserts that name. Known names stay picks.

## Products

- Class / package `<select>` filters (`#first-run-filter-class` / `#first-run-filter-pkg`).
- Type RS622 in `#first-run-product` to list every tracking package. Part-only add ticks all packages of that part.
- `firstRunPicked` Set keeps ticks when the filter hides a row.
- `#first-run-detect`: tracking packages vs disk extras. No scrape. RS622 tracking is SOP8 (RS622XK) + TSSOP8 (RS622XQ). MSOP in tracking is RS2227, not RS622.

## Proof

- `python -m ate.core.check_ui_contract` OK
- Playwright `?v=20260914fr5`: type Lala, click `+ Add Lala`, value stayed Lala (`data-add-name=1`). Filter RS622 lists SOP8 + TSSOP8 only. Detect: tracking SOP8, TSSOP8; disk also MSOP8, TTSOP8 (not offered). Did not Continue. Restored `ate_operator=eugene`.
