---
keywords: [dmm, scpi, -113, header, last_worker.log, dmm_scpi.log, ioz, seelim, leftover-honest]
main_idea: last_worker.log is HTTP RPC only so DMM print() never showed -113. SeeLim 16:32 IOZ PASS n=56 including Vo=1.1 V; screenshot is a reading card not the header. On-screen dialog is leftover Event Log from 15:xx HCOP/NPLC.
---

PREFLIGHT: HIT
reuse: docs/subagents_findings/2026-09-21_dmm-zero-scpi-header.md
spawn: skip

# SCPI header vs logs (SeeLim RS1G126 IOZ 2026-09-21)

## What the files actually contain

| File | What it shows |
|------|----------------|
| `ate/worker/last_worker.log` | `RPC POST / 200` only. No DMM write, no SYST:ERR. |
| SeeLim `sessions/run_log.txt` | `session_2026-09-21_163007` completed 16:32:05 PASS ioz `IOZ_uA=2.593 uA`. |
| `session_2026-09-21_163007.json` | `error: ""`, n=56, includes `VOUT: 1.1`. Screenshot PNG reading card `2.59289 UA`. |
| `session_2026-09-21_160926.json` | Also PASS n=56 (`2.838 uA`). |
| `session_2026-09-21_160633.json` | `status: running`, `steps: []` -- START that never finished (header at 1.1 V, then OK / idle killed PSU). |

Cause of the 16:06 hang was already named: `:HCOP:SDUM:DATA:FORM PNG`, `:SENS:CURR:NPLC`, `:TRAC:CLE`. After the fix, 16:09 and 16:32 both finished 56 current reads. The DMM can still *display* old Event Log rows after SYST:ERR queue is empty.

## Gap

`dmm_setup` used `print()`. Worker stdout is not `last_worker.log`. Next START appends `ate/worker/dmm_scpi.log` (write + SYST:ERR drain). USB Open Session drains `*CLS` + SYST:ERR so leftover queue does not block `:READ?`.

## Operator

Press OK on any leftover Event Log row. Open Session (drain). START IOZ. If a *new* header appears, the token is in `ate/worker/dmm_scpi.log`.
