---
keywords: ovp, ocp, ch1, 2.5v, ldo, en, tutorial
main_idea: Two OVP lamps on OpAmp BUFFER is correct (CH1 and CH2 both 2.5 V). CH1 is not 5 V. Extra CH3 lamps were LDO secretly powering EN at 5.0 V plus AWG 5.5 V. Now CH3=EN 5.0 V / 50 mA, OVP=Vset+0.3, no AWG EN.
---

# 2026-09-14 PSU channel map and OVP lamps

Not a bug that BUFFER lights OVP on CH1 and CH2. Span 5 V = two 2.5 V rails. CH3 OVP on BUFFER or Logic CIN/CPD is a wiring mistake.

What was wrong:

- LDO passed `ovp=6.0` / `5.6` (looser than Vset+0.3; 6.5 hit the 6.0 ceiling).
- LDO also drove AWG DC 5.5 V as EN while PSU CH3 was 5.0 V / 50 mA. Two EN sources; extra lamps.
- Setup hid the map in More/Advanced. Daily `#psu-wiring-hint` now names CH, volts, amps per family.

Map: OpAmp CH1=VDD 2.5 V, CH2=VSS 2.5 V, CH3 OFF, Iset=100 mA, OVP=2.8 V / OCP=0.2 A. Logic CIN/CPD CH1 only. LDO EN = PSU CH3 5.0 V / 50 mA when Continue lists it. Tutorial `docs/tutorial/ATE_TUTORIAL.html#psu-bench` + `images/07-psu-wiring.png`.

Check: `python -m ate.drivers.check_psu_protect` (fails if `ldo.py` has `ovp=6.0` or `_enable_dc`). `python -m ate.core.check_ui_contract` (`paintPsuWiring` + `2.5 V`).
