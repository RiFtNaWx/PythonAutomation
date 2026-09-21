# A15-T03 - PSU/AWG protect hard-fail

**Epic:** EPIC-A15
**PRD:** PRD-001 F22
**Status:** implemented (superseded by A15-T03-psu-protect.md; check_psu_protect green)
**Step:** current: 0 / 3
**Depends on:** none on path (files disjoint from T01). Sequence after T02 in this wave so the inspectable suite is already clickable.
**Model (implement):** composer-2.5
**Model (verify/close):** Grok 4.5 high
**Adversary rule:** R-0003 -- implementer is never the verifier
**GitHub Issues:** do not open

---

## Problem

DUT explode risk. `power_on_protected` exists but defaults are not the lab golden. Unprotected `power_on()` still exists. Founder said "set to the max" -- that means protection always ON and DUT-capped, **not** DP832 30 V / 3 A (that disables useful protection).

Evidence:

- `psu_setup.power_on` -- V then ON, no OVP/OCP
- `psu_setup.power_on_protected` -- if `ovp is None`: `ovp = voltage * 1.1`; if `ocp is None`: `ocp = current_limit` (no +0.1 A)
- `ate/core/param_defaults.py` `PSU_GOLDEN` = `current_limit_a: 0.10`, `ovp_margin_v: 0.3`, `ocp_margin_a: 0.1` -- unused at bring-up
- `opa_tests.py` / `logic_tests.py` / `main.py` do `from psu_setup import *` so the unprotected name stays importable
- AWG: `park_generator_idle` must not `:APPL` (already); `setup_*` still `:OUTP ON` with no DUT peak cap

---

## Acceptance

WHEN any ATE test enables a PSU channel, THE SYSTEM SHALL call a single protected bring-up that always writes OVP and OCP with STAT ON.

WHEN `ovp` / `ocp` are omitted, THE SYSTEM SHALL use golden: OVP = Vset + 0.3 V, OCP = Iset + 0.1 A, Iset default 100 mA (`PSU_GOLDEN`). THE SYSTEM SHALL NOT use `V*1.1` as the default OVP.

WHEN a caller requests OVP/OCP at or above instrument-max (DP832 30 V / 3 A) or requests PROT STAT OFF, THE SYSTEM SHALL hard-fail before `:OUTP ON`.

WHEN `power_on()` is called, THE SYSTEM SHALL raise (do not silently skip protect). Dual-stack `main.py` stays parked; the raise still belongs in `psu_setup.py` because `import *` would keep the hole.

WHEN AWG output is enabled, THE SYSTEM SHALL refuse peak (|offset| + Vpp/2) above DUT Vcc + 0.3 V (Vcc from params, default 5.0 V) and SHALL keep `park_generator_idle` without `:APPL`.

WHEN a runnable check (`python -m ate.core.check_psu_protect` or extend `ate/drivers/check_slew_capture_run.py`) runs, THE SYSTEM SHALL fail if `power_on` still enables output, if default OVP is `voltage * 1.1`, or if golden margins are missing.

Do not pulse `:OUTP OFF` before ON (existing 2026-08-20 rule).

---

## Why it is not a one-liner

Trap: documenting golden in YAML while `power_on_protected` still uses `*1.1`. Trap: deleting only the unused `power_on` while `import *` in `opa_tests.py` still needs a raise. Trap: programming 30 V / 3 A because founder said "max". Trap: rewriting every `setup_sine` instead of one enable helper. Trap: live-hardware check as the only gate -- need a source/self-check that fails offline.

---

## Files likely touched

- `psu_setup.py` -- `power_on` raises; `power_on_protected` golden defaults + refuse instrument-max
- `generator_setup.py` -- one DUT-capped enable; park unchanged
- `ate/core/param_defaults.py` -- read `PSU_GOLDEN` only (no second table)
- `ate/core/check_psu_protect.py` (new, tiny) **or** extend `ate/drivers/check_slew_capture_run.py` with an offline source assert so it can fail without a DP832
- Callers already on `power_on_protected` -- do not rewrite bodies unless they pass ovp=30

Do **not** touch `database.py` path. Do **not** unpark `main.py` rewrite. Do **not** reopen A01-A12.

---

## Step

```
Step: current: 0 / 3
```

1. `power_on` raise + golden defaults + refuse 30 V / 3 A
2. AWG DUT-capped enable; park stays APPL-free
3. Offline self-check fails on the old defaults; idle worker restart

---

## Out

Cloud; mini-scope; A13/A14; new PSU instrument drivers; Comparator bodies; GitHub Issues
