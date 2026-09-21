---
keywords: dmm6500, scpi, -113, conf-curr, nplc, azer, aver, trac, check-all-parts, prompt-guide
main_idea: DMM SCPI errors were extra Keithley headers in dmm_setup_current_continuous. Allowlist is CONF + SENS:FUNC + RANG + READ. Tests already call dmm_setup; synergy is one helper. Guide records AWG -116, DMM -113, OVP 5.6, settle 5s.
---

# DMM allowlist + full PyVISA guide

DMM6500 **-113** is the same class as Rigol **-116**: header the box does not have.

`dmm_setup_current_continuous` sent `:SENS:CURR:NPLC`, `:AZER`, `:AVER:*`, `:TRAC:CLE`. USB Logic already proved SYST:ERR 0 with only `:CONF:CURR:DC 0.01` + `SENS:FUNC 'CURR:DC'` + `:SENS:CURR:DC:RANG 0.01` + `:READ?`. Averaging is the 5 s settle.

All `ate/tests/**` already call `dmm_setup_*` (no raw DMM writes). One file change covers Logic/LDO/LIM/RS0204.

Checks: `python -m ate.core.check_stimulus` (no NPLC/AZER/AVER/TRAC) and `python -m ate.core.check_all_parts` (AST banned writes). Guide: `docs/PROMPT_GUIDE.md` Lessons + Operator scenarios.
