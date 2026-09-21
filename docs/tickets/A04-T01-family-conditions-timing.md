# A04-T01 - Family-scoped conditions + measurement timing

**Epic:** EPIC-A04
**PRD:** PRD-001
**Status:** closed-accepted
**Verified:** 2026-09-03 (R-0003 adversary; Grok 4.5 high; implementer was composer-2.5-fast — not re-used)
**Step:** current: 5 / 5 - closed-accepted after R-0003 verify
**Depends on:** EPIC-A01 / A02 / A03 closed (family load, Logic wraps, add-family slot already in tree)
**Model (implement):** composer-2.5-fast
**Model (verify/close):** Grok 4.5 high (`cursor-grok-4.5-high`)
**Adversary rule:** R-0003 - implementer is never the verifier

---

## Problem

Run-page param catalog and settle/timeout ownership are still OPA-global. Switching to Logic only hides the gain-board panel; the catalog API still serves OPA-only defaults (including G11 / GBW `cfg_g11` steps). New families have no family-local timing surface, so engineers copy OPA settle/timeout literals from `ate/tests/opa/*`.

Evidence:

- `ate/core/param_defaults.py`: `TEST_DEFAULTS` keys are OPA-only (`gbw`, `slew`, `ort`, `vos_sweep`, `ac_*`); GBW fixed steps include `cfg_g11` ("Confirm G11 board..."); `catalog_for_ui(part)` (or equivalent) always returns that OPA catalog (no family argument)
- `ate/worker/server.py`: `list_param_defaults` calls catalog with part only - no family
- `ate/ui/web/app.js`: hides `#panel-gain-boards` when active family is not opamp; `loadParamDefaults` / `list_param_defaults` does not pass family; Logic still inherits the OPA param catalog object
- `ate/core/registry.py` `TestSpec`: no `settle_s` / `timeout` fields (do not invent them here)
- `ate/tests/opa/slew.py`: `timeout_s=6.0, settle_s=1.8`; `ate/tests/opa/settling.py`: `timeout_s=6.0, settle_s=1.5` - body-local OPA hardcodes
- `ate/tests/logic/wraps.py`: thin wraps with Logic-only `fixture_mode`; no Logic condition catalog of their own
- `ate/core/check_family_load.py`: probes opa/logic registry only; does not assert family-scoped catalog or timing ownership

---

## Acceptance

WHEN OpAmp is active, THE SYSTEM SHALL keep the existing OPA param catalog behavior (board-locked G11 gain profiles / GBW steps as today) and existing OPA timing behavior for OpAmp tests (no intentional OpAmp regression).

WHEN Logic is active, THE SYSTEM SHALL expose Logic-relevant condition fields for Run (at minimum: shared bench knobs Logic wraps already need such as `vcc` where applicable) and SHALL NOT require OPA G11 board confirmation for Logic-only runs (no G11 gain-profile UI / no `cfg_g11` step / no G11 RF-RI confirm path as a Logic prerequisite).

WHEN a non-OpAmp family (`logic`, `demo_ingest`, or equivalent) resolves timing or param defaults, THE SYSTEM SHALL NOT fall back to OPA-hardcoded settle/timeout constants from `ate/tests/opa/*` or treat OPA `TEST_DEFAULTS` as the global default for that family.

WHEN the shipped self-check runs, THE SYSTEM SHALL fail if Logic catalog still implies G11 confirmation is required, OR if non-opamp timing/defaults lookup silently uses OPA settle constants as fallback.

WHEN OpAmp is re-selected after Logic, THE SYSTEM SHALL restore OPA catalog + gain panel behavior without registry merge leftovers (A01/A02 invariants still hold).

---

## Why it is not a one-liner

Trap: only CSS-hiding `#panel-gain-boards` while `list_param_defaults` still returns OPA G11 / `cfg_g11` as the universal catalog. Trap: adding `settle_s` / `timeout` onto `TestSpec` as architecture theater without a buyer-visible family surface. Trap: inventing a plugin framework / YAML wizard. Trap: making every unknown family silently inherit `TEST_DEFAULTS` / OPA settle literals (the irreversible tax F5 named). Trap: rewriting Logic or OPA measurement bodies instead of scoping defaults.

---

## Files likely touched

- `ate/core/param_defaults.py` - family-aware `catalog_for_ui(..., family=...)`; family-local timing/defaults lookup; OPA not the fallback for `logic` / `demo_ingest`
- `ate/worker/server.py` - `list_param_defaults` passes active family (or explicit `family` param)
- `ate/ui/web/app.js` - pass family into catalog load; refresh on family switch; Logic Run conditions without G11 confirm path; keep gain panel opamp-only
- `ate/ui/web/index.html` - only if a small Logic conditions surface needs a hook (prefer reuse existing Run param controls)
- `ate/core/check_family_load.py` **or** tiny sibling e.g. `ate/core/check_family_conditions.py` - runnable invariant (extend existing module if cheaper)
- Optional: `ate/tests/logic/` constants beside wraps; optional wire of OPA bodies to opamp family table **without** changing measured OpAmp behavior
- `docs/ATE_PLUGIN.md` - one short note that new families own conditions/timing defaults (no wizard)

Do **not** expand `TestSpec` with timing fields. Do **not** unlock OPA board gain. Do **not** build Level suite or wizard. Do **not** reopen A01-A03 mechanics beyond reading them.

---

## Step

```
Step: current: 5 / 5 - closed-accepted 2026-09-03 (R-0003)
```

Suggested steps for the runner (update the counter as you go):

1. Family-aware catalog + timing lookup in `param_defaults` (OPA unchanged for `opamp`; no OPA fallback for logic/demo_ingest)
2. Wire worker `list_param_defaults` + UI reload on family switch; Logic has no G11 confirm path
3. Optional doc note in `ATE_PLUGIN.md`
4. Runnable self-check green on the invariants below
5. Idle worker restart if needed; leave verify notes for adversary run

---

## Agent prompt

> Implement EPIC-A04 ticket A04-T01 only (family-scoped Run conditions + family-local measurement timing). Repo: PythonAutomation. A01-A03 already in tree. Do not implement other epics.
>
> **Goal:** OpAmp keeps today's param catalog + timing. Logic shows Logic-relevant conditions and does **not** require OPA G11 board confirmation for Logic-only runs. Non-OpAmp families must not inherit OPA settle/timeout hardcodes from `ate/tests/opa/*` via a silent global fallback. No wizard. No `TestSpec` timing dataclass.
>
> **Do:**
> 1. Make param catalog family-aware (`catalog_for_ui` / `list_param_defaults` take family). OpAmp path preserves G11 gain profiles, GBW steps, and existing OPA `TEST_DEFAULTS` behavior.
> 2. For Logic: return Logic-relevant defaults only; do not require G11 gain profiles or GBW step `cfg_g11`. UI must reload catalog on family switch; keep `#panel-gain-boards` hidden when not opamp; Logic-only runs must not present G11 RF/RI confirm as required chrome.
> 3. Add a small family-local timing/defaults lookup (in `param_defaults` or a tiny sibling module). OpAmp may keep body hardcodes in `slew.py` / `settling.py` **or** read the opamp family entry - OpAmp measured timing must stay equivalent. `logic` and `demo_ingest` must resolve without falling back to OPA settle/timeout constants.
> 4. Ship one runnable check (`python -m ate.core.check_family_load` extended, or `python -m ate.core.check_family_conditions`) that **fails** if: (a) Logic catalog still implies G11 confirmation (`cfg_g11` in steps or G11 gain_profiles required), or (b) non-opamp timing/defaults lookup falls back to OPA settle constants. Keep existing A01/A02 family-load assertions green.
> 5. Brief `docs/ATE_PLUGIN.md` note: new family owns its conditions/timing defaults; do not copy OPA settle literals as the platform default.
>
> **Constraints:**
> - Do **not** add `settle_s` / `timeout` fields to `TestSpec`.
> - Do **not** invent a plugin framework or YAML wizard.
> - Preserve OPA category-first order, START session gate, Logic wraps, Level stub, no OPA G11 as Logic fixtures.
> - YAGNI / ponytail: fewest files; deletion over new abstraction layers.
>
> **Out of ticket:** Level suite, wizard, dual-stack delete, rewriting `logic_tests.py` / OPA algorithms, GitHub Issues, A05.
>
> **Model:** implement with composer-2.5-fast. Do not self-close; a different Grok 4.5 high run verifies (R-0003).
>
> After edits that affect the worker, if idle, restart via `restart_ate_worker.bat` per workspace rule. Tell operator Ctrl+F5 if UI catalog chrome changed.

---

## Verify (different run - R-0003)

Implementer must not run this as the close gate. Verifier (Grok 4.5 high) runs:

1. **Runnable:** the shipped check module - must pass, and must be written so it would **fail** if Logic still required G11 confirmation or if non-opamp timing fell back to OPA settle constants. Also re-run prior family-load probes (opamp/logic clear+restore) if folded into the same module.
2. **Static:** catalog / timing lookup is family-keyed; grep that unknown/`logic`/`demo_ingest` path does not `return TEST_DEFAULTS` / OPA settle as default. Confirm `TestSpec` still has no settle/timeout fields.
3. **RPC / UI smoke (idle worker):** `set_family logic` -> `list_param_defaults` (with family) has no required G11 / `cfg_g11`; gain panel stays hidden. `set_family opamp` restores OPA catalog + G11 gain profiles. START still disabled without session. Level still stub.
4. Optional: one Logic wrap still resolves to `logic_tests` (import smoke) without live instruments.

Close only if acceptance WHEN/SHALL statements hold; then update epic ticket index status in the same action.
