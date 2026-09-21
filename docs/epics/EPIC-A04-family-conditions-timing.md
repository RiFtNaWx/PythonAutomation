# EPIC-A04 - Per-family operator conditions + measurement timing

**PRD:** [PRD-001-ate-multi-product-platform](../prd/PRD-001-ate-multi-product-platform.md)
**Repo:** PythonAutomation
**Status:** closed-accepted
**Sliced:** 2026-09-03 (epic-agent Mode A; amended F5 timing constraint)
**Closed:** 2026-09-03 (Mode B: R-0003 + live UI click)
**Tier:** surface (with irreversible family-defaults boundary)
**Depends on:** EPIC-A01 (closed); benefits from A02 Logic wraps (closed); A03 slot closed
**Blocks:** none
**Appetite:** 1 wave
**GitHub Issues:** do not open unless founder opts in

---

## Buyer-visible outcome

Manual / catalog params on Run extend per family (Logic-relevant conditions vs OPA gain profiles), **and** settle/timeout/pulse (or equivalent) is family/test-scoped so a new product does **not** inherit OPA settle constants. No no-code wizard.

---

## Acceptance (from PRD)

> WHEN OpAmp is active, THE SYSTEM SHALL keep OPA param catalog behavior (including board-locked gain profiles) and existing OPA timing behavior for OpAmp tests. WHEN Logic is active, THE SYSTEM SHALL show Logic-relevant condition fields and SHALL NOT require OPA G11 board confirmation for Logic-only runs. WHEN a non-OpAmp family test runs, THE SYSTEM SHALL NOT require that test to use OPA-hardcoded settle/timeout constants from `ate/tests/opa/*`.

---

## Design constraints

- Minimum irreversible fix only: family-scoped param catalog + family-local timing/defaults lookup. Do **not** pre-solve a `TestSpec` `settle_s` / `timeout` dataclass. Do **not** invent a plugin framework or YAML wizard.
- OpAmp keeps category-first board -> channel -> DUT, START session gate, board-locked gain (YAML), existing OPA settle literals in OPA bodies (or read from the opamp family table - either OK if OpAmp behavior unchanged).
- Logic wraps stay thin (`ate/tests/logic/wraps.py` -> `logic_tests.py`). Do not rewrite Logic measurement bodies.
- Non-opamp families (`logic`, `demo_ingest`, later products) MUST NOT fall back to OPA `TEST_DEFAULTS` / OPA settle hardcodes when resolving catalog or timing.
- Level remains stub. Dual-stack `main.py` parked. No GitHub Issues.

---

## Ticket index

| ID | File | Status | One-line acceptance |
|----|------|--------|---------------------|
| A04-T01 | [A04-T01-family-conditions-timing.md](../tickets/A04-T01-family-conditions-timing.md) | closed-accepted (2026-09-03 R-0003) | Family-scoped Run catalog (Logic no G11 confirm) + family-local timing defaults so non-opamp does not inherit OPA settle; OpAmp unchanged; runnable check |

**Ponytail:** one ticket. Conditions UI + timing ownership share the same irreversible boundary (`param_defaults` / family catalog). Splitting would race the same files. No A05 / Level / wizard slice.

---

## File contention

| Area | Tickets | Note |
|------|---------|------|
| `ate/core/param_defaults.py` | T01 | Family-aware catalog + family-local timing/defaults; OPA not global fallback |
| `ate/worker/server.py` `list_param_defaults` | T01 | Pass active family (or explicit family param) into catalog |
| `ate/ui/web/app.js` (+ `index.html` if needed) | T01 | Reload catalog on family switch; Logic conditions without G11/gain confirm path; keep `#panel-gain-boards` hidden off-opamp |
| `ate/tests/logic/` | T01 only if Logic-local defaults live beside wraps | Do not rewrite `logic_tests.py` bodies |
| `ate/tests/opa/slew.py`, `settling.py`, `gbw.py` | optional read-only / wire to opamp table | Keep OpAmp timing behavior; do not force TestSpec fields |
| `ate/core/check_family_load.py` or tiny sibling self-check | T01 | Greppable invariant for Logic catalog + non-opamp timing |
| `ate/core/registry.py` `TestSpec` | **do not expand** for timing fields | Constraint |

Later epics must not reintroduce OPA catalog/timing as the silent default for every family.

---

## Out of epic

- No-code wizard (parked)
- Full Level suite (parked)
- Expanding `TestSpec` with settle/timeout as architecture theater
- Rewriting OPA measurement algorithms
- Deleting legacy `main.py` / dual-stack
- A05 (not required; A04 amendment covers timing)
- GitHub Issues unless founder opts in

---

## Completeness (Mode B - 2026-09-03)

**COMPLETE** - acceptance re-derived from code + runnable check + idle RPC + live UI click (not ticket checkboxes).

Evidence:
1. `python -m ate.core.check_family_load` -> `OK opamp=16 logic=7 restored=16 tests (no cross-family leak); family-scoped catalog/timing OK`
2. RPC: `set_family logic` -> 7 Logic ids, `list_param_defaults` has no G11/`cfg_g11`; `set_family opamp` restores G11 + cfg_g11; `session_status.open=false` START gated
3. UI click (http://127.0.0.1:5174): Logic brand + TP/Tidle/Tdis/Ten/IDD/Vout/CapLoad, gain panel hidden, catalog keys logic-only; OpAmp restore shows G11/BUFFER; Level stub message; START stays disabled
4. `timing_for("logic")` / `timing_for("demo_ingest")` do not equal OPA 6.0/1.5/1.8; unknown family returns empty catalog (no TEST_DEFAULTS fallback)
5. `TestSpec` still has no settle/timeout fields

**Verdict:** closed-accepted. Do not slice Level / wizard / A05 from this close. Next product: ingest family + own `FAMILY_TIMING` / catalog; do not copy OPA settle literals.
