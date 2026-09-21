keywords: dg822, appl-squ, phase, cin, cpd, freq, current, settle
main_idea: CIN speed/flow/delay were wrong because C used the wanted Hz and FREQ? is Error 116. APPL:SQU 4th field is start phase (0), not duty; APPL forces 50% duty. C=I/(V f) must use APPL? Hz. 5 s dwell is wall-clock between sweep points.

## Manual (DG800 Pro)

`:SOURce1:APPLy:SQUare freq,amp,offset,phase` -- example phase 3 deg. APPL overwrites duty to 50%. Do not send `:FUNC:SQU:DCYC` or `:SOUR1:FREQ` (Error 116 on this box).

## What was wrong

- `:FREQ` / `FREQ?` -> Undefined Header 116, AWG Hz did not step (speed)
- C=I/(V f) used the want 1/5/10 MHz so CIN_pF went ~0 when I stayed at the leftover f (flow)
- 5 s settle vs yaml `settle_s: 0.3` plus SAFE IDLE MSO hang after the test (delay)

## Fix

- `setup_square` sends `APPL:SQU freq,vpp,offset,0` (phase 0, 50% duty)
- `applied_freq_hz` parses APPL? `FUNC,freq,...`
- CIN/CPD `_cap_pf` uses that Hz
- Keep `_SETTLE_S = 5.0` on USB (yaml 0.3 is too fast for DMM DCI)

## Checks

- `python -m ate.core.check_walk_order`
- `python -m ate.core.check_stimulus`

Does not prove a live CIN pF vs datasheet with a DUT in the socket. Restart worker only when START is idle.
