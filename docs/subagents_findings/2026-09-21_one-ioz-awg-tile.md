keywords: ioz, path-b, wrap, awg-tile, pnp, logic_dc, seelim, leftover-honest
main_idea: Operator saw two IOZ faces (Path B notes + See Lim wrap src + AWG DC badge) and a dark AWG tile on a live DG822. One TestSpec (`logic_dc._run_ioz`) plus PnP-OK tiles. `.tile.idle` opacity 0.42 was dimming connected AWG when IOZ (PSU+DMM) was ticked.

## Cause
- `list_tests` preferred leftover `snippet_map` `ioz` (Downloads See Lim `current_tests.py`) over `ate/tests/logic/logic_dc.py`.
- `seelim_dc` also registered `ioz` then lost to logic_dc last-import -- still looked like a second body.
- Test program prefixed every DC wave with `AWG DC` even when `required_instruments` had no AWG.
- Header tiles used session mapping only. After restart mapping was empty. Tick IOZ then `.tile.idle { opacity: 0.42 }` dimmed connected AWG.

## Fix
- `source_for_spec`: ate/tests wins wrap. Hide wrap src on Test program.
- Drop seelim `ioz` register. IOZ notes = OE-off PSU+DMM, not IOFF.
- Tiles = PnP-OK + last Discover + session. Do not dim `.on` tiles.
- Operator fixture labels drop "Path B DC".

## Proof
- `python -m ate.core.check_ui_contract`
- `python -m ate.core.check_add_test`
- `python -m ate.core.check_stimulus`
- `python -m ate.core.check_visa`

## Leftover-honest
IOFF (VCC=0 SeeLim wrap) stays a different id on RS1G126. snippet_map still has wrap rows for Detect. AWG green from PnP is USB present, not *IDN Open Session.
