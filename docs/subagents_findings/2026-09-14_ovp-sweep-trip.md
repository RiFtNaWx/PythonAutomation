---
keywords: ovp, trip, reduce-limit, vin-sweep, power_on_protected, dp832, ldo, iq
main_idea: Mid-test OV lamps plus 'reduce the limit' were real. power_on_protected wrote VOLT while the previous Vset+0.3 OVP was still armed, so VIN 2.0->5.0 tripped DP832. Raise ceiling, then V, then tighten.
---

# 2026-09-14 OVP trip on live voltage steps

OVP lamps lighting = PROT:STAT ON (armed). That part is intended.

What was a bug: LDO IQ/VINMIN/IEN (and any live sweep) call `power_on_protected` again with output still ON. Old order was VOLT then OVP. Channel at 2.0 V had OVP 2.3 V; next step 5.0 V > 2.3 V -> DP832 OV trip, output drops, OVP number on the panel jumps. Looks like "reduce the limit" mid-test.

Fix in `psu_setup.power_on_protected`: write OVP/OCP to 6.0 V / 0.5 A first, then V/I, then tighten to Vset+0.3 / Iset+0.1. Steady-state trip is still DUT-capped. Check: `python -m ate.drivers.check_psu_protect` (2.0->5.0->2.0 must not trip; final OVP 2.3).
