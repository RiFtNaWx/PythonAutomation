# A15-T02 - Category change loads a different suite

**Epic:** EPIC-A15
**PRD:** PRD-001 F22
**Status:** implemented (superseded by A15-T02-category-switch.md; stub now clears registry)
**Step:** current: 0 / 3
**Depends on:** A15-T01 (path parse must already know operator)
**Model (implement):** composer-2.5
**Model (verify/close):** Grok 4.5 high
**Adversary rule:** R-0003 -- implementer is never the verifier
**GitHub Issues:** do not open

---

## Problem

Family rail already switches packages (A01). Campaign apply already calls `family_for_component` + `load_family` (A09/F20). Gaps remain:

- `family_for_component` last-resort `return "opamp"` steals OpAmp for unknown folders (stub Power/Comparator must stay empty -- `check_new_product` already asserts Power -> `""`).
- `set_db_context` when `wanted` is empty: "folders saved, family left as-is" -- previous OpAmp/Logic tests stay on Run.
- JS `familyFromComponent` falls back to `c || "opamp"`.
- New product stub note is honest, but Apply can still show the last live suite.

Founder: product category change must load a different suite (family / tests / conditions / folders). Do not invent Comparator or Power measurement bodies.

---

## Acceptance

WHEN the operator selects a **live** RUN-IC class (OpAmp / Logic / Analog SW) via left rail, campaign Apply, or New product, THE SYSTEM SHALL `load_family` that key and SHALL list only that family's tests + fixture catalog + conditions (reuse A01/A04; do not rebuild the rail).

WHEN the operator selects a **stub** class (`run_ic.yaml` `live: false`: Comparator, Power, Interface, Vref, Data conversion, Clock), THE SYSTEM SHALL present an empty test list and no OPA gain boards, and SHALL NOT keep the previous family's tests registered.

WHEN `family_for_component("Power")` or `"Comparator"` is called, THE SYSTEM SHALL return `""` (not `"opamp"`). WHEN `family_for_component("OpAmp")` is called, THE SYSTEM SHALL still return `"opamp"`.

WHEN folders are created for a stub class, THE SYSTEM SHALL still use the T01 5-level path under that component (e.g. `Comparator/.../{operator}/Version_1`) with empty `enabled_tests`.

WHEN `python -m ate.core.check_new_product` and `python -m ate.core.check_family_load` run, THE SYSTEM SHALL fail if a stub component maps to `opamp` or if switching to a stub leaves OpAmp test ids loaded.

---

## Why it is not a one-liner

Trap: only changing the campaign breadcrumb. Trap: `family left as-is` on stub. Trap: last-resort `return "opamp"`. Trap: writing Comparator.py bodies. Trap: racing T01 by assuming 4-level `root()`.

---

## Files likely touched

- `ate/core/database.py` -- `family_for_component` last-resort; `set_context` must not steal
- `ate/worker/server.py` -- `set_db_context` / `ensure_product` / `set_family`: empty suite when `wanted` is `""` (clear/reload, do not leave prior family)
- `ate/ui/web/app.js` -- `familyFromComponent`; `applyDb` / New product must refresh tests even when `family_error`; stub hint already exists for Level -- reuse
- `ate/core/check_new_product.py` / `check_family_load.py` -- stub must not steal OpAmp; live Logic still not empty
- `ate/config/run_ic.yaml` -- read only unless a label is wrong; do not set stub `live: true`

Do **not** add `ate/tests/comparator`. Do **not** change PSU (T03). Do **not** reopen A01-A12.

---

## Step

```
Step: current: 0 / 3
```

1. Stop last-resort OpAmp steal; stub -> empty suite
2. Wire Apply / New product / rail so leftover tests cannot remain
3. Checks + Ctrl+F5; idle worker restart

---

## Out

Comparator/Power bodies; A13/A14; cloud; T01 migrate rewrite; T03 protect; GitHub Issues
