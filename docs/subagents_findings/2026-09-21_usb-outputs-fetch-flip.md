# keywords: failed-to-fetch, pic-steal, golden_auto, empty-workbook, fill-excel, csv, screenshot, session-identity
# main_idea: START must pin the Setup campaign and never applyDb; Excel/JSON/CSV/PDF/photos write to that session folder; PIC sheet_map.operator cannot steal; empty xlsx rebuilds standard golden (Path B golden_auto, OpAmp *_filled.xlsx).

## Problem
After USB ICC, leftover-honest gaps: START Failed to fetch (applyDb + loadTests), worker campaign flipped Eugene -> Chun Tak (PIC) after DONE, empty workbook fill failed, pictures only if Written screenshot_from, Path B operators expected *_filled.xlsx.

## Fix
- UI: rpc retries once on fetch/network/Failed; START never applyDb; params() pins component/part/package/operator/version; fill_workbook + export_datalog send params().
- Worker: `_pin_run_campaign` on run_sequence / run_sequence_async; `_session_bound_ctx` for Excel/STS so PIC cannot steal the write folder.
- database.set_context: do not copy sheet_map.operator. `_write_session` / record_step / end_session fill+paste use `context_from_identity(session.context)`.
- Path B excel_lock: dest missing/empty/corrupt (<64 bytes or load fail) creates a new golden_auto workbook. Still never `_filled.xlsx`.
- OpAmp fill: empty src rebuilds standard golden then copy_golden sidecar.
- runner: empty screenshot_from infers mso (MSO/SCOPE) else dmm (DMM). SIM still skips MSO shots.

## Checks
`python -m ate.core.check_ui_contract`
`python -m ate.core.check_walk_order`
`python -m ate.core.check_tags_datalog`
`python -m ate.core.check_session_values`
`python -m ate.core.check_logic_dc`

## leftover-honest
- Scale-wave G00/G02/G04/G86/2G08/2G32 UNCONFIRMED HOLD
- leftover-13 iso/xtalk/ron/settling/noise
- Dual launch.pyw
- Path B has no *_filled.xlsx by design
- USB START auto_continue=False
- MSO screenshots skipped on SIM
