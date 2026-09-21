---
keywords: [dmm, scpi, -113, syst-cle, event-log, sens-func, ioz, leftover-honest]
main_idea: Operator still saw the header after a PASS IOZ because Keithley Event Log is not SYST:ERR. Fix is skip extra SENS:FUNC, SYST:CLE once at Open Session / current setup, then START cannot pop a new -113.
---

PREFLIGHT: HIT
reuse: docs/subagents_findings/2026-09-21_dmm-scpi-header-log.md, 2026-09-21_dmm-zero-scpi-header.md
spawn: skip

# Dismiss leftover DMM header before START

Live writes on IOZ: `*CLS`, `:CONF:CURR:DC`, `:READ?`, `SYST:ERR?`. Extra `:SENS:FUNC` after CONF was still on the voltage path and is -113-class on 1.7.16a. The on-screen dialog after a PASS run is Event Log history; `SYST:CLE` once clears it. Do not send SYST:CLE on every `:READ?`.
