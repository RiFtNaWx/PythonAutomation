---
keywords: live-usb, walker, ignore-dmm, run_sequence_async, leftover-13, leftover-honest, goal-open, check_live_usb, discover-empty
main_idea: Idle worker. UI RPC discover + open_session both returned {}. No USB serials. Did not resume START (would replay Missing instruments). n=218 ok=1. Leftover 13 unchanged. Goal OPEN.
---

# Live USB walk ignore DMM (2026-09-15)

PREFLIGHT: HIT. RPC-only. No this-process PyVISA. No NI list_resources. Did not UpdateGoal complete.

## This sitting

session_status: busy=false, pending=null, open=true mapping=`{}` (ghost). Not a human START. Closed it.

Same UI RPCs as `app.js` Discover / Open Session:

- `rpc("discover")` ~5s -> `{}` (did not hang; no second discover)
- `rpc("open_session")` -> `{}` session open with empty map
- closed empty session again

**mapping serials:** none. Need PSU+AWG+MSO USB; DMM optional.

**resumed:** no. Missing-instruments FAILs stay retryable (`check_live_usb.py` RETRYABLE). A mapping-empty FAIL is not a success.

**this sitting attempted/ok/fail:** 0 / 0 / 0 (no START)

**live_usb_stamps:** n=218 ok=1 (lm358/sssr only USB pass)

## Leftover 13 (unchanged)

lm358/rs358/rs622 settling; rs0302 i2c_ron; rs2227 usb_ron/usb_iso/usb_xtalk; rs2323 ron/iso/xtalk; rs358/rs622/rs8551 noise.

## Goal

**OPEN.**

## Next (human, under 2 min)

Power + USB on DP832 / DG800 / MSO5072. Close Ultra Sigma. Console Discover until tiles show USB PSU+AWG+MSO. Then `python -m ate.core.check_live_usb resume`.
