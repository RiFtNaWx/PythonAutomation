---
keywords: prompt-guide, scpi, pyvisa, undefined-header, 116, dg822, rag, idd, ovp, 5.6
main_idea: Speak-to-code lives in docs/PROMPT_GUIDE.md and must grep this repo (psu/generator/dmm/scope_setup) instead of web SCPI. IDD OVP is 5.6 V not 5.5 because Vset=OVP (or 10% of 5.0) trips DP832.
---

# Speak translator + IDD OVP 5.6

Lab errors we already hit:

- Rigol **Undefined SCPI Header Error 116** = instrument does not have that header. Almost always a DG4000 / Keysight / web paste.
- DG822 Pro "remote command not included in the library" = same class. Golden is `generator_setup.py` only.

Do not stand up a vector RAG. `docs/PROMPT_GUIDE.md` Speak table + grep those four setup files is the lookup.

IDD (`ate/tests/logic/eugene_cap.py` `run_idd`): VCC corners include 5.5 V. Passing `ovp=5.5` trips immediately. 10% of 5.0 V is also 5.5. Use **5.6 V**. AWG Input A DC 5.5 V stays. DUT ceiling is still `OVP_ABS_MAX_V = 6.0`.

Check: `python -m ate.core.check_add_test` fails if `ovp=5.5` remains in eugene_cap.
