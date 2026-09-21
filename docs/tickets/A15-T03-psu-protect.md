# A15-T03 - PSU/AWG protect hard rules

**Epic:** EPIC-A15
**Status:** implemented

## Acceptance

WHEN `power_on_protected` runs, THE SYSTEM SHALL program OVP and OCP with PROT:STAT ON, default Vset+0.3 V and Iset+0.1 A, refuse instrument-max (ceil 6 V / 0.5 A), and fail closed if STAT readback is off.

WHEN `power_on` is called for DUT work, THE SYSTEM SHALL raise (use power_on_protected).

SAFE IDLE order stays AWG OFF -> PSU OFF -> scope STOP.
