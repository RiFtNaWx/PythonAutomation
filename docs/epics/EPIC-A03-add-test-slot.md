# EPIC-A03 - Add-test slot for any family

**PRD:** [PRD-001-ate-multi-product-platform](../prd/PRD-001-ate-multi-product-platform.md)
**Repo:** PythonAutomation
**Status:** closed-accepted
**Closed:** 2026-09-03 (prd-agent Mode B feedback intake F5; acceptance re-derived from working tree, not tickets)
**Tier:** capability
**Depends on:** EPIC-A01 (closed-accepted)
**Blocks:** none
**Appetite:** short wave (landed in-tree before formal slice)
**GitHub Issues:** do not open unless founder opts in
**Tickets:** none filed (capability shipped ahead of epic-agent slice; no ticket files for this epic)

---

## Buyer-visible outcome

An engineer following `docs/ATE_PLUGIN.md` can add a family package (or ingest one) without editing `runner.py`. After worker refresh/restart, the family appears on the rail and its `register(TestSpec)` tests list. One self-check fails if opa-only hard-import returns in `runner.py`.

---

## Acceptance (from PRD) - code evidence 2026-09-03

> WHEN a new `TestSpec` is registered via the family package `__init__` import convention and the worker is restarted, THE SYSTEM SHALL include it in `list_tests` / Run UI without editing `runner.py` beyond the A01 family loader. WHEN the self-check is run, THE SYSTEM SHALL fail if opa-only hard-import returns.

| Claim | Evidence |
|-------|----------|
| No opa hard-import in runner | `ate/core/runner.py` imports/calls `load_family` only; `check_family_load._runner_uses_family_loader` asserts no `import ate.tests.opa` |
| Family table is data-driven | `registry.refresh_family_table`: builtins + `pkgutil` under `ate.tests.*` + `ate/config/extra_families.yaml` |
| Third family without runner edit | `ate/tests/demo_ingest/` + `extra_families.yaml` key `demo_ingest` -> `ate.tests.demo_ingest`; `load_family` resolves via table |
| Ingest path | `ate/core/family_ingest.import_family`; worker RPC `import_family`; Setup UI Import family (`ate/ui/web/index.html` / `app.js`) |
| Doc slot | `docs/ATE_PLUGIN.md` (family package, register, map, ingest, restart) |
| Self-check opa-hard-import gate | `python -m ate.core.check_family_load` (parent ran this turn; prior pass `OK opamp=16 logic=7 restored=16`; this agent shell blocked on path apostrophe) |

**Verdict:** COMPLETE / closed-accepted. Platform add-test / add-family slot exists. Do not re-slice A03.

---

## Residual (non-blocking; does not reopen)

- `check_family_load` still probes only opamp/logic builtins. It does **not** yet assert `load_family("demo_ingest")` or another extra family. Mechanism is proven by files + yaml; optional verify hardening may land under a later ticket if epic-agent wants it - not a reopen of A03.

---

## Out of epic / parked

- Per-family operator conditions and **measurement timing** (settle/timeout/pulse) -> EPIC-A04 (amended 2026-09-03 F5)
- Full Level suite -> PARKED
- No-code wizard -> PARKED
- TestSpec timing dataclass as a pre-solved design -> not required by this close; A04 names the constraint only
