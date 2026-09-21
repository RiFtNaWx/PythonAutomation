---
keywords: sheet_class, level-shifters, logic-series, linear-regulator, low-noise-opamp, inventory
main_idea: Qualification Main category text is SoT. RS0204 is Level Shifters (category=level) with ate_suite=logic. UI must not copy ate_suite into the RUN-IC class dropdown.
---

# 2026-09-09 Sheet class classification

Map:

- Low Noise / General / Precision Op-Amp -> opamp
- Analog Switch -> analog_switch
- Logic Series -> logic
- Level Shifters -> level (RS0204 live suite still logic)
- Linear Regulator -> power (stub)

Check: `python -m ate.core.check_new_product`
