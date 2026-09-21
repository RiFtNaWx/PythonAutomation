---
keywords: [dmm, scpi, -113, header, buffer, nplc, filter, screenshot, hcop, ch3, ioz, leftover-honest]
main_idea: DMM6500 1.7.16a pops Undefined Header on NPLC/AVER/TRAC/HCOP. That dialog blocks :READ? at IOZ Vo=1.1 V; OK then SAFE IDLE kills PSU. Fix is drain+skip banned headers, host 5-read mean, screenshot none|dmm reading card never HCOP, AWG CH3 never ON.
---

PREFLIGHT: PARTIAL
reuse: docs/subagents_findings/2026-09-21_ioz-dmm-hcop.md, 2026-09-14_dmm-scpi-allowlist.md, 2026-09-21_awg-undefined-header.md
spawn: skip (parent implemented from cited files)

# Zero DMM SCPI header

## What the operator saw

IOZ Vo sweep stuck at 1.1 V. DMM showed SCPI header. After OK, PSU outputs went off. Screenshot was the error dialog. AWG/third generator channel must not open (DG822 is 2-ch; OUTP3 is -116).

## Cause

Same class as Rigol -116: DMM6500 1.7.16a does not have NPLC / AZER / AVER / TRAC:CLE / HCOP. Sending them queues -113, freezes :READ? until the dialog is dismissed, then the run excepts and `_power_down` / reopen idle turns PSU OFF.

Hardware filter/NPLC on this firmware cannot be set over USB. Span/rdgs on the box still follows the MENU Rate. Console filter is host-side.

## Fix (live product)

- `dmm_setup.py`: `is_banned_dmm_scpi`, `dmm_write_ok` skips banned (no dialog), `dmm_drain_errors` before READ, `clear_active_buffer` is `*CLS` + drain (never TRAC:CLE), `dmm_read` / `dmm_read_avg` = clear then n=5 mean. `nplc` only sleeps 20 ms * NPLC between those reads.
- Screenshot: Parameters none | DMM | MSO. DMM writes a reading-card PNG in lab_sheet `IOZ/` while rails are on. Never HCOP.
- IOZ: AWG `stop_output` (CH1/CH2 only). PSU CH3 stays OE inactive 0 V. Capture only when `screenshot_from=dmm`.
- Checks fail-closed if a live helper `.write`s a banned header.

## Operator

1. Ctrl+F5 on http://127.0.0.1:5174
2. Parameters: screenshot DMM or none. DMM avg N=5. Write.
3. DMM MENU (optional): Rate 1 NPLC, Filter ON count 5. Do not expect USB to set those.
4. START IOZ. Do not press OK on a header dialog -- there should be none.

## Leftover-honest

- Front-panel pixels over USB (HCOP) still leftover on 1.7.16a.
- Goldens still contain NPLC/TRAC/OUTP3. Path C that triggers those functions can still -113/-116. Do not rewrite goldens.
- Live USB START of IOZ uA is the proof; checks are SIM + source scan.
