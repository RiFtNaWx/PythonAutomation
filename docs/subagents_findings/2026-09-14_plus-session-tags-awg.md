---
keywords: plus-session, tags, kind-board, no-tags-tab, awg, psu, stimulus, squ, sine, pulse, logic
main_idea: + Session writes session JSON only (no VISA). Tags tab removed; Kind=board + Value is Add board. Test rows show AWG shape. SIM APPL SQU/SIN/PULS/DC and PSU ON/OFF proven by check_stimulus.
---

# 2026-09-14 + Session, tags Kind=board, AWG shapes

PREFLIGHT: PARTIAL. Reuse combo-tags, usb-live, sim-loopback. Spawn: skip.

## + Session

Writes `#Test_Database/.../sessions/session_*.json` with optional run label. Does not Discover, Open Session, or power PSU/AWG. START still needs Open Session (USB) or Open SIM.

## Tags (no fifth tab)

Setup More: Kind dropdown (`board` / `board_type` / `tag` / `task`) + Value list. Picking a Value saves `board:LOGIC-SC70-REV1`. Logic SC70-5 vocab added. Chip x removes. Import/search stays collapsed.

## Waves

`list_tests.stimulus` badges SQU/SIN/DC/PULS/off. Tests bake APPL; Advanced freq/amp is only some OpAmp bodies. `check_stimulus` programs SIM AWG+PSU and asserts bus + idle.

USB START still needs KEEP USB and operator Continue. Do not Select-all on first live pass.
---
