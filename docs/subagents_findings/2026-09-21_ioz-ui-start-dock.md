---
keywords: ioz, start, run-dock, parameters-details, screenshot-dmm, path-b-handoff, applyDb, continue, leftover-honest
main_idea: START looked dead because WAIT + applyDb delay swallowed the click. Sticky right START becomes Continue; IOZ skips recipe/save popups; DMM-only tests default screenshot none.
---

# IOZ UI START dock + fewer popups

## Cause

1. `#btn-start` sits above a long Test program list. Operator scrolled to tick IOZ, then had to scroll up. No sticky control.
2. START always `await applyDb()` which reloads tests (seconds on OneDrive). That wait looks like a dead click. If worker already WAIT, START returned `"Run already in progress"` on `#notice-banner` or silently after `runPollActive`.
3. `#panel-logic-dc` dumped product_model JSON (not the Recipe tab). Path B IOZ also dumped `format_handoff_begin` into Continue, then a second "save paths" popup after PASS. OpAmp VOS has fixture + DUT only.
4. Parameters `screenshot_from` was none|MSO. `include_screenshot` defaulted MSO even for IOZ (PSU+DMM). Header tiles stay the Open Session map, so AWG/MSO green looks like "run everything".
5. DELAY = `_wait_settled_current_ua`, not a dead START.

## Fix

- `#run-dock` sticky right-middle START; WAIT -> Continue; busy -> notice + Run tab.
- `clickStartOrContinue` + `campaignAlreadyApplied` skip applyDb.
- Parameters `<details class="test-spec-edit">` closed until click.
- screenshot_from DMM when TestSpec needs DMM; IOZ default none (no Keithley dump; leftover-honest).
- `path_b_handoff`: skip IOZ begin dump; skip success save-paths for all Path B.
- `#panel-logic-dc` collapsed `logic-dc-fold`. `#run-need-hint` names ticked instruments.

## Does not prove

Live USB IOZ uA this click (need Open Session + Continue on DUT). Keithley screen dump still does not exist.
