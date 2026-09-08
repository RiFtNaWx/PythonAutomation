# PRD-001 - ATE multi-product operator platform

**Product:** PythonAutomation ATE (operator console + worker)
**Owner:** founder
**Status:** A01-A06 closed-accepted. A07-A12 implemented (R-0003 pending -- verify wave, not this implement slice). Do not reopen A01-A16. A13 Excel merge-center and A14 xyflow stay PARKED (numbers reserved). EPIC-A15/A16 implemented. **WIP: EPIC-A17** (F24 tags + session datalog JSON + auto-paste + golden workbook).
**Repos in scope:** this repo (`PythonAutomation` / origin `jian-hong/Python_Automation_JH`); LA-1 recipe source at `C:\Users\OoiJianHong\Downloads\LabAutomation-1\LabAutomation-1` (reference, not a second runtime)
**Created:** 2026-08-19
**Updated:** 2026-09-08 (F24 founder: tags beside model, STS session JSON, auto-paste into sheet_map, golden format check)
**Epic home:** A17 at `docs/epics/EPIC-A17-tags-session-datalog.md` (READY). A16-A15 implemented; A12-A07 R-0003 pending; A06-A01 closed. Do **not** open GitHub Issues for epics/tickets unless the founder later opts into issue tracking on `origin`. Ticket files under `docs/tickets/`.

---

## 1. Press release

### One console. Many product families. Same operator muscle memory.

**Subheading:** Lab operators and characterization engineers switch OPA, Logic, and later Level apps from a left rail - without losing the Continue gates, session lock, or registered tests they already trust.

**Problem:** "We have an OPA ATE that works on the bench. The Test Database already has folders for Logic and Level, and the campaign dropdown lists them - but picking Logic still shows OPA gain boards and OPA tests. Adding a new product family means editing the runner import list and living with a header that still says OPA ATE. This is an OPA app wearing a database tree, not a platform."

**Solution:** A product-family plugin contract. Each family (OpAmp, Logic, Level-later) owns its registered `TestSpec` package, fixture catalog, and operator-visible labels. The left rail selects the family; the worker loads that family's package; the Run page lists that family's tests. OPA behavior that already shipped (category-first board -> channel -> DUT order, operator Continue short tags, START disabled until Open Session, board gain locked in YAML for OPA fixtures) stays the default for the OpAmp family. Engineers add a new test by `TestSpec` + `register()` in the family package and restarting the worker - not by patching a hard-coded OPA import forever.

**Quote:** "I switched to Logic, saw Logic timing tests, and the OPA G11 board chips were gone. When we added one more OPA sweep, it showed up after worker restart without touching runner.py's family list." - characterization lead, internal pilot (aspirational)

**Call to action:** A01-A11 shipped or implemented. Independent R-0003 on A07-A11 (Grok 4.5 high). RS0204 recipes still missing -- ask the author.

---

## 2. FAQ

### External

- **What is shipping in this slice?** A multi-family operator console (A01-A06) plus A07: engineers change workbook photo boxes in one YAML SoT (or the Results layout editor); the website reconstructs that DUT x channel grid from campaign graphs/screenshots for side-by-side / overlay compare. Not a second Excel system; not DataLogger replacement; not a canvas scope-trace renderer.
- **Will OPA runs change for operators who stay on OpAmp?** No intentional behavior change. Category-first order, gates, session START lock, and existing OPA tests remain. Regression against the 2026-08-19 live demo is a fail for A01/A02.
- **Can we add Level this quarter?** Level gets an empty (or stub) family slot in the contract so the rail can show it without lying. Full Level characterization suite is out of scope for this PRD.
- **Do we need new instruments?** No. Discover / Open Session / START gate stay. Empty Discover still correctly blocks START.
- **Is this a no-code product?** Not yet. Python `register()` is the supported add-test path. YAML/UI condition knobs are A04 surface; a wizard is parked.

### Internal

- **What could make this fail?** Shipping a left rail that only changes the `#Test_Database` campaign path while registration still hard-imports OPA only - that is today's bug dressed as a feature. Second failure mode: rewriting fixture modes into a shared free-gain dial and breaking OPA board-lock semantics. Third (post-A03): a new family that silently reuses OPA settle/timeout constants because timing lives only inside OPA bodies.
- **What are we assuming?** (1) `TestSpec` + `register()` + `all_tests()` remain the extension point. (2) `logic_tests.py` functions are wrappable without inventing a full Logic suite. (3) One worker process, one active family at a time for v1 (switch family clears or reloads registry). (4) Prior OPA improvements listed in readiness stay. (5) Family slot for later products exists (A03); per-family **measurement timing** is not yet a first-class surface (A04).
- **What would we have to be right about?** That "family" is the irreversibility boundary - harder to reverse than UI chrome or one Logic wrapper. If we keep OPA-only imports while painting a rail, every later family pays a tax. After A03, the next irreversible tax is OPA settle constants leaking into every new product.
- **Why not delete `main.py` now?** Dual stack is debt, not the platform claim. Deleting legacy without a family contract just moves Logic callers into the wrong place. Parked.
- **GitHub Issues?** `origin` exists but this wave keeps epic sketches and (later) local ticket files in-repo unless the founder opts into Issues.

---

## 3. Out of scope

Explicit park / refuse for this PRD:

- Inventing a full Logic characterization suite beyond wrapping existing `logic_tests.py` entry points into `ate/tests/logic` `TestSpec`s
- Full Level product app (beyond an empty/stub family slot so the rail is honest)
- Hardware appearing when Discover returns `{}`
- Rewriting PyVISA helpers (`instruments.py` session stack) as a platform rewrite
- No-code test wizard
- Tauri native shell as a required delivery (scaffold may exist; not this PRD's success gate)
- STM relay bank / arbitrary gain dial
- Deleting legacy `main.py` / `opa_tests.py` / teaching rewrite of `TEST_DESIGN.md` away from legacy (doc sync may follow; not blocking)
- Linear project board; GitHub epic/ticket Issues unless founder opts in
- Changing the START-disabled-until-Open-Session rule
- Unlocking OPA board gain as a free numerical control (YAML lock stays correct for OPA fixtures)
- Pre-solving a `TestSpec` timing dataclass / plugin framework / YAML wizard in this PRD (A04 named the **constraint**; closed without a wizard)
- Inventing full OpAmp measurement suites for Noise / PSRR / CMRR / AOL / EMIRR / VOL / etc. (A05 stub/list; A06 does not invent recipes where LA-1 has none)
- Replacing ATE DataLogger / pass-fail log wholesale with LA-1 DataLogger; inventing a second Excel reporting stack
- Copying whole LabAutomation-1 tree into `ate/` as a parallel runtime
- RS1G07 / RS1G14 / RS1G08 Logic part yaml + DC sweeps (same Logic family later; not A06)
- Lim RS2323 as a new family (later; not Level stub; not A06)
- PowerOn MOSFET fixture automation; Noise flicker / noise_bucket bodies
- Lim RS2323 family this wave (unparked as EPIC-A10; not Level stub)
- RS0204 measurement bodies until the author Python exists (campaign/workbook is EPIC-A11; do not wrap RS29511)
- Reconstructing analog scope traces from CSV into a new chart library (A07 uses captured graph/screenshot images)
- Drag-drop Excel clone / Figma layout editor (A07 is YAML SoT + Results grid + cell text save)
- Cloud sync of Test_Database / sessions (F22 park)
- Mini-scope / CSV chart reconstruct of analog traces (F22 park; A07 uses captured images)
- Circuit drawing / schematic viz (F22 park)
- Drag-drop waveform editor (F22 park)
- Programming PSU OVP/OCP to instrument-max (DP832 30 V / 3 A) -- that is not "set to the max"; it disables useful protection
- Inventing Comparator / Power / Interface / Vref / Data conversion / Clock measurement bodies (stub RUN-IC classes stay empty suites)

---

## 4. Success assertion

Testable from the operator / engineer seat:

> **WHEN** an operator picks a product family on the left rail (OPA / OpAmp or Logic), **THE SYSTEM SHALL** load that family's registered tests and fixture catalog into the Run console, and **SHALL NOT** present OPA-only gain boards (G11 / G_NEG100 / VOS research chips) as if they applied to Logic.
>
> **WHEN** an engineer adds a new test via `TestSpec` + `register()` inside the active family's package and restarts the worker, **THE SYSTEM SHALL** list that test in the console without requiring an edit to `runner.py` beyond the single family-package import (or family plugin table) introduced by EPIC-A01.
>
> **WHEN** no instrument session is open, **THE SYSTEM SHALL** keep START disabled.

Code anchors (baseline 2026-08-19; **re-verified working tree 2026-09-03**):

- Family load (not opa-only): `ate/core/runner.py` calls `load_family`; `ate/core/registry.py` `FAMILY_PACKAGES` + `refresh_family_table` + `ate/config/extra_families.yaml` + pkgutil
- START gate: `ate/ui/web/app.js` start button disabled until session open
- Logic registered: `ate/tests/logic/wraps.py` (7 wraps); A02 closed-accepted 2026-08-20
- Add-family slot: `docs/ATE_PLUGIN.md`, `ate/core/family_ingest.import_family`, Setup Import family, `ate/tests/demo_ingest`
- Timing constraint (closed A04): family-local catalog/timing; OPA settle may remain body-local for OpAmp
- Lab-report sync (closed F10 / A05): live RS622 xlsx sheets, `sheet_map.yaml` excel_sheet, and OpAmp `TestSpec.lab_sheet` agree; `check_lab_report_sync` fails on drift; Noise is a RuntimeError stub (no full suite); paste still ORT+Settling only
- F11 / F13: EPIC-A06 closed-accepted - BUFFER SSSR / LSSR / NoPhaseReversal are LA-1 wraps (not RuntimeError stubs); workbook remains characterization SoT; PowerOn / Noise / PSRR stubs remain parked
- F14: EPIC-A07 - photo layout SoT is campaign `sheet_map.yaml` `paste.photos` (not hardcoded A91 dicts in `lab_report.py`); Results page reconstructs the grid and compares latest vs previous shots
- F22 (this slice): campaign path gains an Operator segment; category change loads that class's suite (empty if stub); PSU/AWG protection is DUT-capped and hard-fails if skipped

---

## 5. Code-verified baseline

### 5a. Original (2026-08-19)

Do not treat as aspirational:

| Area | State | Evidence |
|------|-------|----------|
| Worker / UI | Live ping v0.2.2; Setup/Run/Results | readiness finding; ports 8766 / 5174 |
| Modular core | `TestSpec`, `register()`, runner, fixture modes, operator gate, DB tree | `ate/core/*`, `ate/fixture/*` |
| OPA automated | slew, settling, gbw, ort, vos_sweep, ac_gain_check, ac_vin_sweep | `ate/tests/opa/*` |
| OPA stubs | 9x `RuntimeError` stubs | `ate/tests/opa/stubs.py` |
| Operator flow | category-first board -> channel -> DUTs; short tags | `ate/core/runner.py`, findings 2026-08-07 |
| Platform gap (then) | campaign dropdown changes folder; tests do not | UI + opa-only import |
| Readiness scores | compile 95, UI 88, OPA tests 82, new OPA test slot 70, new OPA part 55, Logic/Level apps 28, no-code 18, left-rail 12 | founder + readiness finding |
| Dual stack | `ate/` console vs legacy `main.py` / `opa_tests.py` / `logic_tests.py` | repo root |

Prior improvements **must be kept** (non-negotiable for OpAmp family): category-first order, Continue popup short tags, safe-idle before gates, START session gate, existing OPA automated tests, board gain locked for OPA fixtures.

### 5b. Re-verified working tree (2026-09-03)

Nearness artifact checked (F8): live workbook sheets on `RS622XK_Lab_Report_TTSOP.xlsx` (Summary, Checklist, + 15 test sheets incl. **Noise**) vs registered OpAmp `TestSpec.lab_sheet` + external `_manifest/sheet_map.yaml` (path in `ate/config/bench.yaml`). Family rail + Import family remain clickable; report honesty is the next buyer-visible gap.

| Area | State | Evidence |
|------|-------|----------|
| A01 family switch | closed-accepted | `docs/epics/EPIC-A01-family-plugin-left-rail.md` |
| A02 Logic wraps | closed-accepted; 7 wraps | `ate/tests/logic/wraps.py`; finding 2026-08-20 |
| Family table | builtins + pkgutil + yaml | `registry.refresh_family_table`, `ate/config/extra_families.yaml` |
| Third family | `demo_ingest` present | `ate/tests/demo_ingest/`, yaml key |
| Ingest RPC/UI | live path | `ate/core/family_ingest.py`, worker `import_family`, Setup button |
| Self-check | opa hard-import forbidden; opa/logic probe only | `ate/core/check_family_load.py` (does **not** yet assert third family - residual non-blocking) |
| Timing | A04 closed; OpAmp body-local OK | finding 2026-09-03_a04-t01-mode-b |
| Lab report sync | **closed (F10 / A05)** | workbook / sheet_map / lab_sheet honest; Noise stub listed; sync check fails on `Slew` drift; paste stretch (Slew/GBW) still out |
| BUFFER stubs | SSSR / LSSR / NoPhaseReversal still RuntimeError | `ate/tests/opa/stubs.py`; LA-1 has `test_SSR` / `test_LSR` / `test_NPR` (finding 2026-09-03_labautomation-1-scale) |
| Two reports | keep both roles | LA-1 DataLogger = pass-fail log; ATE `RS622XK_Lab_Report_TTSOP.xlsx` + sheet_map = characterization workbook SoT |
| Level | stub | `ate/tests/level` empty suite |
| Dual stack | parked | legacy `main.py` still present |
| Operator path | **done (F22/A15)** | `DbContext.root()` = component/part/package/operator/version; migrate + All view-only |
| PSU protect | **done (F22/A15)** | `power_on_protected` golden V+0.3 / I+0.1; PROT readback; unprotected `power_on` raises |

`python -m ate.core.check_family_load` this agent turn: shell wrapper failed on path apostrophe; parent already ran the module this turn. Prior recorded pass: `OK opamp=16 logic=7 restored=16 tests (no cross-family leak)`.

---

## 6. Model / dispatch law (this wave)

Recorded for agents; not a product feature.

| Role | Model |
|------|-------|
| prd-agent, epic-agent, verify / close | Grok 4.5 high (`cursor-grok-4.5-high`) |
| ticket-runner (this wave, founder override) | cheapest (`composer-2.5-fast`) |
| Claude Code (separate product) | Opus only. Cursor **cannot** dispatch Claude Code. |

**F-0009:** one ticket-runner per working tree. Do not dual-lane.

**Current:** **EPIC-A15** READY (F22). Do not reopen A01-A12. Do not unpark A13/A14. Independent R-0003 on A07-A12 is a **separate verify wave**, not this implement slice.

---

## 7. Epic sketches (irreversibility order)

Epics are sketches here. Epic-agent owns ticket files. Appetite default: one focused agent wave unless noted.

Ordering law: irreversibility, not value. A01 before A02 before A03 before A04 before A05 before A06 before A07.

### EPIC-A01 - Product-family plugin boundary (left rail switches real apps)

| Field | Value |
|-------|-------|
| Tier | boundary (with visible surface so WIP is inspectable) |
| Repo | this repo |
| Contract impact | additive (new family plugin / load API; OPA remains default path) |
| Depends on | none |
| Blocks | EPIC-A02, EPIC-A03, EPIC-A04 |
| Appetite | 1 wave |
| Status | **closed-accepted** (2026-08-19) |

**Buyer-visible outcome:** Operator sees a left-rail product switcher (OpAmp / Logic; Level may appear as stub). Selecting a family changes tests + fixture catalog + brand copy, not only the DB breadcrumb.

**Acceptance:**
> WHEN the operator selects Logic on the left rail, THE SYSTEM SHALL stop listing OpAmp-only fixture gain boards as applicable and SHALL expose only that family's registered tests (may be empty until A02). WHEN the operator selects OpAmp, THE SYSTEM SHALL restore the existing OPA test list and OPA fixture catalog without regressing category-first gates or the START session lock.

**Design constraints (for tickets, not pre-solved here):**
- Replace opa-hardcoded register hook with family-package load (plugin table or `ate.tests.<family>` convention).
- Registry must be family-scoped or cleared+reloaded on switch (do not silently merge OPA+Logic ids).
- Preserve START disabled when session is not open.
- Human-inspectable: founder can click the rail and see the Run page change.

**File contention note:** A01 owns runner register hook, registry family scoping if needed, and left-rail UI. Later epics must not re-harden opa-only imports.

---

### EPIC-A02 - Logic family wraps existing `logic_tests.py`

| Field | Value |
|-------|-------|
| Tier | capability |
| Repo | this repo |
| Contract impact | additive |
| Depends on | EPIC-A01 |
| Blocks | none hard; improves A01 demo |
| Appetite | 1 wave |
| Status | **closed-accepted** (2026-08-20) |

**Buyer-visible outcome:** Switching to Logic lists Logic tests backed by existing `logic_tests.py` functions (e.g. timing / TP paths already in-tree), not OPA stubs.

**Acceptance:**
> WHEN Logic is selected and at least one Logic `TestSpec` is registered, THE SYSTEM SHALL list those tests on the Run page. WHEN the operator runs a wrapped Logic test with an open session, THE SYSTEM SHALL invoke the existing logic test function path (wrap, do not rewrite the measurement body in this epic).

**Out of epic:** inventing new Logic characterization beyond wrap; Level suite.

---

### EPIC-A03 - Add-test slot for any family

| Field | Value |
|-------|-------|
| Tier | capability |
| Repo | this repo |
| Contract impact | none (docs + convention + self-check; may add tiny family `__init__` pattern) |
| Depends on | EPIC-A01 |
| Blocks | none |
| Appetite | short wave |
| Status | **closed-accepted** (2026-09-03 from working tree; epic file `docs/epics/EPIC-A03-add-test-slot.md`) |

**Buyer-visible outcome:** An engineer following one doc can add a test under any family package; after worker restart it appears. One runnable self-check fails if the convention breaks.

**Acceptance:**
> WHEN a new `TestSpec` is registered via the family package `__init__` import convention and the worker is restarted, THE SYSTEM SHALL include it in `list_tests` / Run UI without editing `runner.py` beyond the A01 family loader. WHEN the self-check is run, THE SYSTEM SHALL fail if opa-only hard-import returns.

**Code evidence (2026-09-03):** `ate/config/extra_families.yaml` + `refresh_family_table` + pkgutil; `family_ingest.import_family` + RPC + Setup UI; `docs/ATE_PLUGIN.md`; `demo_ingest` family; `runner` -> `load_family`; `check_family_load` opa-hard-import gate.

**Residual (non-blocking):** self-check does not yet assert a third family (`demo_ingest`). Mechanism proven by files; optional verify hardening later - does not reopen A03.

**Secondary (explicitly not blocking A03):** new OPA part YAML authoring remains lower priority (readiness score ~55).

**Roadmap timing (F5 sense 1):** slot for later DUT families without rewriting `runner.py` - **satisfied by this closed epic**. Do not slice Level/full suites now.

---

### EPIC-A04 - Per-family operator custom conditions (incl. measurement timing)

| Field | Value |
|-------|-------|
| Tier | surface |
| Repo | this repo |
| Contract impact | additive |
| Depends on | EPIC-A01 (family context); benefits from A02 for Logic params; A03 slot closed |
| Blocks | none |
| Appetite | 1 wave |
| Status | **closed-accepted** (2026-09-03 Mode B; epic `docs/epics/EPIC-A04-family-conditions-timing.md`; ticket A04-T01) |

**Buyer-visible outcome:** Manual / catalog params already used on Run extend per family (Logic conditions vs OPA gain profiles), **and** settle/timeout/pulse (or equivalent measurement timing) is family/test-scoped so a new product does **not** inherit OPA settle constants. No no-code wizard.

**One-liner (amended):** Per-family Run conditions + per-family/per-test measurement timing without a wizard; new families must not silently reuse OPA settle/timeout hardcodes.

**Acceptance:**
> WHEN OpAmp is active, THE SYSTEM SHALL keep OPA param catalog behavior (including board-locked gain profiles) and existing OPA timing behavior for OpAmp tests. WHEN Logic is active, THE SYSTEM SHALL show Logic-relevant condition fields and SHALL NOT require OPA G11 board confirmation for Logic-only runs. WHEN a non-OpAmp family test runs, THE SYSTEM SHALL NOT require that test to use OPA-hardcoded settle/timeout constants from `ate/tests/opa/*`.

**Constraint (not a pre-solved design):** Today `TestSpec` has **no** `settle_s` / `timeout` / timing fields; timing lives inside OPA/Logic measurement bodies; `ate/core/param_defaults.TEST_DEFAULTS` is OPA-only. Epic-agent must pick the **minimum** irreversible fix (family-local defaults, body params, or a small shared helper) - do **not** invent a plugin framework or YAML wizard unless the ticket acceptance requires a buyer-visible knob.

**Out of epic:** no-code wizard (parked); full Level suite (parked); expanding `TestSpec` as architecture theater without an operator/engineer-visible outcome.

**F5 sense 2 (measurement timing):** closed via A04 (2026-09-03). Do not reopen.

---

### EPIC-A05 - OpAmp lab-report / sheet_map / TestSpec sync

| Field | Value |
|-------|-------|
| Tier | boundary (report honesty) + visible surface (console lists missing sheets; runnable check) |
| Repo | this repo |
| Contract impact | additive (sync check + honest stubs/map; no breaking worker RPC contract) |
| Depends on | EPIC-A01 (OpAmp family load); A02-A04 closed, not reopened |
| Blocks | none hard; later paste/automation for missing sheets depends on honest map |
| Appetite | 1 wave |
| Status | **closed-accepted** - 2026-09-03 F10 R-0003; epic `docs/epics/EPIC-A05-lab-report-sync.md` |

**One-liner:** Make OpAmp lab workbook sheets, `sheet_map.excel_sheet`, and `TestSpec.lab_sheet` agree - and fail a check when they do not; list missing sheets (stub OK) without inventing full Noise/PSRR suites.

**Buyer-visible outcome:** Operator / engineer can trust that every workbook **test** sheet (not Summary/Checklist) either has a matching registered `lab_sheet` or is explicitly listed as missing; `sheet_map` names match the live xlsx; console does not pretend a sheet is covered when it is not.

**Acceptance (testable):**
> WHEN the OpAmp lab-report sync check runs against the active campaign workbook + `sheet_map` + registered OpAmp `TestSpec.lab_sheet` values, THE SYSTEM SHALL FAIL if (1) a workbook test sheet (excluding Summary and Checklist) has no matching `TestSpec.lab_sheet`, OR (2) a registered `lab_sheet` is missing from the workbook, OR (3) a `sheet_map` `excel_sheet` value disagrees with the live xlsx sheet name it claims to map. WHEN a workbook test sheet such as Noise has no matching spec, THE SYSTEM SHALL list it in the console (a registered stub that raises RuntimeError is OK; inventing a measurement suite is not).

**Optional stretch (same epic only if no second framework):** Automated tests that already capture screenshots (Slew Rate, GBW) MAY paste into the workbook via existing `sheet_map` photo anchors / `lab_report` helpers (same pattern as ORT/Settling). Skip if it forces a new paste framework.

**Design constraints (for tickets, not pre-solved here):**
- Source of truth for sheet names = live xlsx (evidence: RS622XK_Lab_Report_TTSOP.xlsx). Fix `sheet_map` and/or `lab_sheet` strings to match; do not invent alternate names.
- Add Noise (and any other xlsx-only sheet) as stub or explicit listed gap - do **not** implement Noise/PSRR/CMRR/AOL measurement bodies.
- Runnable check: prefer extend `ate/core/check_family_load.py` or a tiny sibling module; must be greppable and CI/local runnable.
- Do not reopen A01-A04. Do not slice Level. Logic sheet_map / #Test_Database out unless proven to block OpAmp honesty.
- Part yaml id drift (BUFFER stub ids vs yaml; G1001 `vos_lab`) is note-only unless it blocks the sync check.

**Out of epic:** full Noise/PSRR/CMRR/AOL/EMIRR automation; Level; Logic report sync as a second product claim; GitHub Issues; wizard.

**File contention note:** Likely `ate/tests/opa/stubs.py`, `ate/reporting/*` / paste helpers, external campaign `_manifest/sheet_map.yaml`, and one check module. Epic-agent must keep ticket count ponytail-small and avoid racing the same file across tickets.

---

### EPIC-A06 - LA-1 BUFFER wraps into workbook use cases

| Field | Value |
|-------|-------|
| Tier | capability (measurement recipes) + visible surface (workbook screenshots / paste) |
| Repo | this repo |
| Contract impact | additive (replace RuntimeError stubs with thin LA-1 wraps; no breaking worker RPC) |
| Depends on | EPIC-A05 closed (honest sheet_map / lab_sheet); A01-A04 closed, not reopened |
| Blocks | none hard; later PowerOn / Noise / PSRR stay parked |
| Appetite | 1 wave |
| Status | **closed-accepted** - 2026-09-03 F13 R-0003 Mode B |

**One-liner:** Thin-wrap LA-1 SSSR / LSSR / NPR into OpAmp TestSpecs so operator runs write screenshots under Test_Database and paste into the characterization workbook where sheet_map already has anchors.

**Buyer-visible outcome:** Operator with open session can run Small/Large Signal Step Response and No Phase Reversal and get real LA-1 recipes (not stub RuntimeError); screenshots land under Test_Database; when sheet_map has photo anchors, paste via existing `lab_report.embed_photo` pattern. Workbook remains the characterization SoT; DataLogger stays the pass-fail log (do not replace wholesale).

**Nearness (F11 / F13):** Artifact checked = live registry + `ate/tests/opa/buffer_steps.py` + R-0003 finding `docs/subagents_findings/2026-09-03_a06-t01-r0003-verify-pass.md`. BUFFER SSSR/LSSR/NPR are LA-1 wraps (not RuntimeError stubs). Workbook remains characterization SoT.

**Acceptance (testable):**
> WHEN the operator runs SSSR, LSSR, or NPR (NoPhaseReversal) with an open instrument session, THE SYSTEM SHALL invoke the corresponding LabAutomation-1 recipe path via a thin ATE wrap (not raise the A05-era RuntimeError stub) and SHALL save screenshots under Test_Database. WHEN `sheet_map` has photo anchors for that test, THE SYSTEM SHALL paste via the existing `lab_report.embed_photo` pattern (same family as ORT/Settling). WHEN GBW screenshots are already captured on disk and sheet_map has GBW photo anchors (A45 grid), THE SYSTEM MAY paste them in the same epic if it reuses existing helpers without inventing a second paste framework. WHEN PSRR / CMRR / AOL / VOL / EMIRR have no LA-1 RS622 recipe, THE SYSTEM SHALL leave those stubs as stubs.

**Design constraints (for tickets, not pre-solved here):**
- Source recipes: `C:\Users\OoiJianHong\Downloads\LabAutomation-1\LabAutomation-1` (`test_SSR` -> SSSR, `test_LSR` -> LSSR, `test_NPR` -> NoPhaseReversal). Prefer thin wrap over rewriting bodies. LA-1 SSR is newer than repo-root `opa_tests.test_SSR` - do not prefer the weaker legacy path.
- Keep ATE-native: `slew.py`, `settling.py`, `ort.py`, `gbw.py` (`measure_gbw`). Do not replace them with LA-1 `test_sr` / `test_gbw` / `test_settlingTime` / `test_ORT`.
- Two reports: LA-1 DataLogger / `RS622_results.xlsx` = pass-fail log; ATE `RS622XK_Lab_Report_TTSOP.xlsx` + sheet_map = characterization workbook (founder SoT). Do not replace DataLogger wholesale. Do not invent a second Excel system.
- sheet_map already has SSSR/LSSR photo anchors; PhaseReversal / NoPhaseReversal map may lack paste photos - wrap + Test_Database screenshots still required; paste only where anchors exist.
- Optional same epic: GBW `place_photos` using existing sheet_map A45 grid if screenshots already on disk and no second framework.
- Do not reopen A01-A05. Do not slice RS1G07/14/08 part yaml, Lim RS2323 family, PowerOn MOSFET, Noise flicker, or full PSRR/CMRR/AOL/VOL/EMIRR suites.

**Out of epic:** RS1G ingest; Lim family; PowerOn; Noise bucket; PSRR suites; Level; DataLogger replacement; copying whole LA-1 tree; GitHub Issues; wizard.

**File contention note:** Likely `ate/tests/opa/stubs.py` (or new thin wrap modules), LA-1 recipe import/path bridge, `ate/reporting/*` / embed_photo callers, external `sheet_map.yaml` photo anchors only if missing. Epic-agent must keep ticket count ponytail-small; one ticket preferred if wrap+paste share the same path.

---

### EPIC-A07 - Photo-grid SoT + Results waveform preview

| Field | Value |
|-------|-------|
| Tier | visible surface (Results reconstruct) + capability (one layout SoT for paste) |
| Repo | this repo |
| Contract impact | additive RPC `layout_preview` / `save_photo_layout` + GET `/shot`; paste reads sheet_map |
| Depends on | EPIC-A06 closed (BUFFER paste exists); A05 sheet_map honesty |
| Blocks | none hard; later PowerOn / Noise / PSRR stay parked |
| Appetite | 1 wave |
| Status | **WIP** - 2026-09-03 F14 |

**One-liner:** Engineers change workbook image boxes in one place (`sheet_map.yaml` `paste.photos`); the Results page reconstructs that grid from Test_Database graphs/screenshots so they can compare waveforms and save new Excel cells from the laptop.

**Buyer-visible outcome:** Operator opens Results, picks a test (SSSR / LSSR / Settling / ORT / ...), sees the same 4-DUT x ChA/ChB (or POS/NEG) photo grid the workbook uses, clicks a cell to compare latest vs previous capture (side-by-side or overlay), edits the Excel anchor, Save writes `sheet_map.yaml`. Next paste uses those cells. No second Excel writer. No new port (5174 + 8766).

**Nearness (F14):** Artifact checked = duplicated `_SSSR_PHOTO_ANCHORS` / `_LSSR_PHOTO_ANCHORS` / `_SETTLING_*` in `ate/reporting/lab_report.py` vs live `_manifest/sheet_map.yaml` `paste.photos`; Results page is a last-run table only; graphs already live under `{Test}/DUT_N/graphs` and `screenshots`.

**Acceptance (testable):**
> WHEN an engineer changes a photo box, THE SYSTEM SHALL have one SoT: campaign `_manifest/sheet_map.yaml` `tests.<key>.paste.photos` (Python paste helpers SHALL read that map, not a second hardcoded A91 dict). WHEN the operator opens Results and selects a test that has `paste.photos`, THE SYSTEM SHALL reconstruct that DUT x channel grid from Test_Database `graphs/` (preferred) or `screenshots/` and SHALL let them compare the latest capture to the previous one. WHEN they save a new Excel cell from that page, THE SYSTEM SHALL write that cell back into `sheet_map.yaml` so the next `embed_photo` uses it.

**Design constraints (for tickets, not pre-solved here):**
- Modular Python: `ate/reporting/photo_layout.py` is the only paste-anchor lookup. `lab_report.place_*` calls it. Document the YAML path in `docs/ATE_PLUGIN.md`.
- Reconstruct with existing PNGs/JPGs on the website (operator console :5174). Do not add a chart library or CSV waveform renderer this wave.
- Serve images from worker GET `/shot` under the campaign root only (`screenshots` / `graphs`). Ports stay 8766 / 5174.
- Overlay compare may use CSS mix-blend; do not invent OpenCV alignment this wave.
- Do not reopen A01-A06. Do not slice PowerOn / Noise / PSRR / RS1G / Lim / Level. Do not replace DataLogger.

**Out of epic:** CSV-to-canvas traces; drag-drop Excel clone; GBW paste wiring (anchors already in yaml; paste caller is later); stub measurement bodies.

**File contention note:** `ate/reporting/lab_report.py` (delete hardcoded photo dicts), new `photo_layout.py`, `ate/worker/server.py`, `ate/ui/web/*`. One ticket.

---

### EPIC-A08 - DMM session + every mapped test runnable

| Field | Value |
|-------|-------|
| Tier | capability (DMM) + visible surface (Setup map coverage) |
| Repo | this repo |
| Contract impact | Discover classifies DMM; Instruments.dmm optional; mapped OpAmp sheets no longer RuntimeError |
| Depends on | A05 sheet_map honesty; A07 photo_layout paste |
| Appetite | 1 wave |
| Status | **implemented** (R-0003 pending) - 2026-09-03 F15 |

**One-liner:** First setup Discover shows MSO/PSU/AWG/DMM; every `sheet_map` test has a real TestSpec; VOL/Logic IDD use DMM when present.

**Acceptance:**
> WHEN Discover runs, THE SYSTEM SHALL classify DMM (DMM6500 / 344xx / Keithley) into the mapping and Open Session SHALL expose `instr.dmm` when found (optional, like PSU/AWG). WHEN a sheet_map test exists, THE SYSTEM SHALL register a matching `lab_sheet` that does not raise the old stub RuntimeError. WHEN VOL / Logic IDD/VOUT/cap_load run without DMM, THE SYSTEM SHALL fail with missing instruments (honest). WHEN Setup loads, THE SYSTEM SHALL show map coverage for every sheet_map key.

**Out of epic:** Full analog PSRR/CMRR/AOL lab recipes; PowerOn MOSFET fixture; Lim RS2323; DataLogger replace.

---

### EPIC-A09 - Logic campaign platform (Ariff / Soo)

| Field | Value |
|-------|-------|
| Tier | capability (campaign YAML) + visible surface (Logic Apply campaign) |
| Repo | this repo |
| Contract impact | Logic parts own specs/timing/enabled tests in YAML; Ariff DC TestSpecs; family-aware coverage |
| Depends on | A01 rail; A02 wraps; A04 timing; A08 DMM |
| Appetite | 1 wave |
| Status | **implemented** (R-0003 pending) - 2026-09-03 F16 |

**One-liner:** One Logic rail; Soo RS29511 vs Ariff RS1G08 differ by campaign/part YAML, not forked Python.

**Acceptance:**
> WHEN operator Applies a Logic campaign, THE SYSTEM SHALL use that campaign sheet_map for map coverage. WHEN part is RS29511, THE SYSTEM SHALL list Soo-enabled tests only. WHEN part is RS1G08, THE SYSTEM SHALL list Ariff timing + DC TestSpecs. WHEN Logic is active, THE SYSTEM SHALL show fixture LOGIC (not OPA G11). Lim stays out.

**Out of epic:** Lim RS2323; copying LA-1 Ariff/Soo/Lim trees; RS1G07 cpd/cin; Level; DataLogger replace; A01-A08 reopen.

---

### EPIC-A10 - Lim RS2323 + open inventory fill

| Field | Value |
|-------|-------|
| Tier | capability (new family) + inventory honesty |
| Repo | this repo |
| Contract impact | builtin `lim` family; RS2323 campaign; RS1G07/14 Logic YAML; Level empty campaign |
| Depends on | A09 Logic PaaS; A08 DMM |
| Appetite | 1 wave |
| Status | **implemented** (R-0003 pending) - 2026-09-03 F17 |

**One-liner:** Lim rail runs RS2323 current tests with Continue gates; remaining open Logic parts + Level stub are campaign-checkable.

**Acceptance:**
> WHEN Family Lim is selected, THE SYSTEM SHALL list iplus / leakage_off / leakage_on / input_leakage. WHEN rewiring is required, THE SYSTEM SHALL use operator Continue not `input()`. WHEN open-inventory check runs, THE SYSTEM SHALL confirm Lim + RS1G07/14 + Level folders.

**Out of epic:** RS0204 measurement bodies (campaign is A11); Lim configurations.py import; cpd/cin; Level suite; DataLogger replace; A01-A09 reopen.

---

### EPIC-A11 - RS0204 campaign + workbook honesty

| Field | Value |
|-------|-------|
| Tier | capability (new Logic part) + report honesty |
| Repo | this repo |
| Contract impact | additive part yaml + TestSpecs; no new family |
| Depends on | A09 Logic PaaS |
| Appetite | 1 wave |
| Status | **implemented** (R-0003 pending) - 2026-09-03 F18 |

**One-liner:** Logic Apply RS0204 uses the real lab workbook; 16 dual-rail bodies (VCCA/VCCB) run without Soo/RS29511.

**Acceptance:**
> WHEN Logic campaign RS0204/TSSOP14 is Applied, THE SYSTEM SHALL list 16 tests whose lab_sheet matches the live workbook. WHEN an RS0204 test runs, THE SYSTEM SHALL use ate/tests/logic/rs0204.py dual-rail bodies (PSU CH1=VCCA, CH2=VCCB) and SHALL NOT import Soo.logic_tests.

**Out of epic:** QFN/UQFN extra campaigns; DataLogger replace; A01-A10 reopen.

---

### EPIC-A12 - Ariff latest Logic into ATE

| Field | Value |
|-------|-------|
| Tier | family wrap completeness |
| Repo | this repo |
| Contract impact | additive |
| Depends on | A09 Logic campaign; A02 wraps |
| Appetite | 1 wave |
| Status | **implemented** (R-0003 pending) - 2026-09-04 F21. Do not reopen. |

**One-liner:** Operator on Logic / RS1G08 sees the full Ariff DC + VOH/VOL set. Soo RS29511 stays Soo-only. No `import Ariff.*`.

**Out of epic:** Excel merge-center (A13); xyflow (A14); LDO; copying Ariff Repo; reopen A01-A11.

---

### EPIC-A13 - Excel merge-center / OneDrive import (RESERVED PARKED)

| Field | Value |
|-------|-------|
| Status | **PARKED** (number reserved F21; do not slice) |
| Unlock | founder unparks after A15; not this wave |

### EPIC-A14 - xyflow / canvas waves (RESERVED PARKED)

| Field | Value |
|-------|-------|
| Status | **PARKED** (number reserved F21; do not slice) |
| Unlock | founder unparks after A15; not this wave |

---

### EPIC-A15 - Operator folder + category suite + PSU/AWG protect

| Field | Value |
|-------|-------|
| Tier | foundation (path) + boundary (protect) + visible surface (Setup tree / suite) |
| Repo | this repo |
| Contract impact | additive (path + identity field; no breaking worker RPC version bump -- callers gain optional `operator`) |
| Depends on | A01 family rail (closed); A09 campaign apply (implemented). Does **not** depend on A07-A12 R-0003 |
| Blocks | later campaign writers that assume 4-level roots |
| Appetite | 1 wave (3 tickets, one seam each) |
| Status | **READY** - 2026-09-08 F22. Epic file `docs/epics/EPIC-A15-operator-folder-safety.md` |

**One-liner:** Insert `{Operator}` before `{Version_N}` in `#Test_Database`, migrate existing trees, put who-ran into session identity, make RUN-IC category actually load that class's suite (empty if stub), and hard-fail PSU/AWG bring-up that skips DUT-capped OVP/OCP.

**Buyer-visible outcome:** Setup campaign path shows Component / Part / Package / Operator / Version. Picking Logic vs OpAmp vs Analog SW (or a stub class) changes tests + conditions + folders. Session JSON names the operator. Rails come up with OVP/OCP always ON at Vset+0.3 V / Iset+0.1 A (Iset default 100 mA) -- never DP832 30 V / 3 A.

**Nearness (F22):** Artifact checked = live `ate/core/database.py` `DbContext.root()` + Setup campaign dropdowns + `owners.yaml` picker + `psu_setup.power_on_protected` + `param_defaults.PSU_GOLDEN`. Operator console is the buyer surface (ports 8766 / 5174). A green family-load check is not this slice; the operator must see the extra folder and a different suite.

**Acceptance (testable):**
> WHEN a campaign is created or Applied, THE SYSTEM SHALL use `#Test_Database/{Component}/{Part}/{Package}/{Operator}/{Version_N}/` and SHALL migrate existing `Package/Version_N` trees into that shape. WHEN `begin_session` writes `sessions/*.json`, THE SYSTEM SHALL include operator identity (who ran which tests on which part/version). WHEN the operator changes RUN-IC product category / family, THE SYSTEM SHALL load that class's tests + fixture catalog + conditions (empty suite if `live: false`) and SHALL NOT leave the previous family's tests on screen. WHEN PSU output is enabled, THE SYSTEM SHALL program OVP and OCP every time at DUT-capped golden (OVP=Vset+0.3 V, OCP=Iset+0.1 A, Iset default 100 mA) and SHALL hard-fail rather than call unprotected `power_on()` or program instrument-max (30 V / 3 A). WHEN AWG output is enabled, THE SYSTEM SHALL keep existing park-without-APPL idle and SHALL refuse amplitude that is not DUT-capped.

**Out of epic:** A13 Excel; A14 xyflow; cloud sync; mini-scope/CSV reconstruct; circuit drawing; drag-drop waves; no-code wizard; Comparator/Power measurement bodies; dual-stack `main.py`; reopen A01-A12; GitHub Issues.

---

### EPIC-A16 - Detect / wrap / copy / +Version / +Session

| Field | Value |
|-------|-------|
| Tier | capability (AST detect + wrap) + visible surface (Setup + buttons) |
| Repo | this repo |
| Contract impact | additive RPCs; A03 `register(TestSpec)` slot stays closed |
| Depends on | A03 add-test slot (closed); A15 operator path (implemented) |
| Blocks | none hard |
| Appetite | 1 wave (2 tickets) |
| Status | **implemented** - 2026-09-08 F23 |

**One-liner:** Scan `ate/tests` + configured golden roots for unmatched `def test_*`; wrap clean ones (no `input()`) into family `TestSpec`s; copy/enable onto another same-family part; Setup `+` creates next `Version_N` and a new run-record session JSON. No Monaco / in-browser code editor.

**Buyer-visible outcome:** Setup lists detected golden functions (blocked if dirty). Operator wraps a clean one into the active family and enables it on the current part -- Run shows the checkbox after reload. Operator copies test ids from part A to part B (same family only). `+` beside Version creates `Version_N+1`. `+` beside Session writes `sessions/session_*.json` without START / VISA.

**Nearness (F23):** Artifact checked = Setup (Import family, New product, Version dropdown) has no + Version / + Session / detected table; `ensure_product` always `Version_1`; family_ingest rejects raw `def test_*`; rs1g07.yaml parks cpd/cin; pasted `test_cpd`/`test_cin` use `input()` so must be blocked until rewritten.

**Acceptance (testable):**
> WHEN Setup loads, THE SYSTEM SHALL list unmatched `def test_*` from `ate/tests` and any configured golden root that exists, without executing those files. WHEN a listed function contains `input(`, THE SYSTEM SHALL mark it blocked and SHALL NOT wrap it. WHEN the operator wraps a clean detected function into the active family and enables it on the current part, THE SYSTEM SHALL show that test on Run after family reload without editing `runner.py`. WHEN the operator copies tests from part A to part B in the same family, THE SYSTEM SHALL append those ids to B's `enabled_tests` and SHALL refuse a different family. WHEN the operator clicks + Version, THE SYSTEM SHALL create the next `Version_N` under the current operator folder. WHEN the operator clicks + Session, THE SYSTEM SHALL write a new `sessions/session_*.json` without requiring START.

**Out of epic:** in-browser code editor; auto-run dirty goldens; clone RS0204 dual-rail bodies onto RS1G07; real RS1G07 CPD/CIN physics; A13/A14; no-code wizard; reopen A01-A15; Level/Comparator bodies.

---

### PARKED (not epics this PRD)

| Item | Unlock condition |
|------|------------------|
| No-code test wizard | A03 slot proven; founder asks for non-Python authors -- F23 detect/wrap is **not** the wizard |
| Tauri native shell as success gate | Web console meets family switch; packaging appetite opens |
| STM relay / free gain | Hardware + DR; must not break OPA YAML lock until then |
| Delete legacy `main.py` | A02 Logic path proven through `ate/`; dual-stack tax measured |
| Full Level suite | Separate PRD or amendment after A01 stub slot exists (F5: keep slot; do not slice Level now) |
| Full Noise / PSRR / CMRR / AOL / VOL / EMIRR measurement suites | After A06 BUFFER wraps + founder appetite; stubs stay stubs when LA-1 has no RS622 recipe |
| Lim RS2323 extra family | **Unparked EPIC-A10** |
| RS0204 measurement bodies | Author Python not in LA-1; campaign/workbook is EPIC-A11 |
| PowerOn MOSFET fixture automation | After A06; fixture-heavy; separate appetite |
| Noise flicker / noise_bucket body | After A06; LA-1 commented/incomplete; not A06 |
| Excel merge-center / OneDrive import | **A13 reserved PARKED** (F21/F22) |
| xyflow / canvas waves | **A14 reserved PARKED** (F21/F22) |
| Cloud sync of Test_Database | F22 park |
| Mini-scope / CSV analog reconstruct | F22 park (A07 uses captured images) |
| Circuit drawing / schematic viz | F22 park |
| Drag-drop waveform editor | F22 park |
| Comparator / Power / Interface / Vref / Clock / Data conversion bodies | Stub `live: false`; do not invent suites |
| PSU OVP/OCP at instrument-max (30 V / 3 A) | Refused -- DUT-capped golden only |

---

## 8. Blocking vs later (product claim)

**Blocking for "platform" claim (this PRD):**

1. Product-family plugin contract + left rail that switches tests + fixture catalog + runner family import (EPIC-A01) - **done**
2. Preserve OPA operator flow (constraint on A01+; verified by regression) - **done**
3. Add-test slot for any family: docs + convention + one self-check (EPIC-A03) - **done** (2026-09-03)

**Worth doing, not blocking platform claim, but next irreversible tax:**

4. YAML/UI custom conditions per family **including measurement timing** (EPIC-A04) - **done** (2026-09-03)
5. No-code wizard (parked)
6. Tauri shell (parked)
7. STM relay (parked)
8. Delete legacy main (parked)

**A02** was the honest demo partner for A01 (Logic not empty). A01-A04 closed-accepted.

**Next irreversible tax (F8 / F10):**

9. OpAmp lab workbook / `sheet_map` / `TestSpec.lab_sheet` honesty + runnable sync check (EPIC-A05) - **closed-accepted** (F10)

**Next irreversible tax (F11 / F13):**

10. LA-1 BUFFER wraps (SSSR / LSSR / NPR) into characterization workbook use cases (EPIC-A06) - **closed-accepted** (F13). Keep ATE-native slew/settling/ORT/GBW. Do not replace DataLogger.

11. Photo-grid SoT + Results waveform reconstruct/compare/save (EPIC-A07) - **implemented** (F14); R-0003 pending.

12. DMM in Discover/session + every sheet_map test has a non-stub run path (EPIC-A08) - **implemented** (F15); R-0003 pending.

13. Logic campaign platform: `#Test_Database/Logic` + per-part YAML (RS29511 / RS1G08) + Ariff DC slots (EPIC-A09) - **implemented** (F16); R-0003 pending.

14. Lim RS2323 family + open inventory RS1G07/14 + Level stub campaign (EPIC-A10) - **implemented** (F17); R-0003 pending.

15. RS0204 Logic campaign + live workbook + dual-rail bodies (EPIC-A11) - **implemented** (F18 campaign, F19 bodies); R-0003 pending.

16. Ariff latest Logic wraps (EPIC-A12) - **implemented** (F21); R-0003 pending.

**F22 (done):**

17. Operator folder before Version + migrate + session identity; category loads that class's suite; PSU/AWG DUT-capped protect hard-fail (EPIC-A15) - **implemented**.

**Next irreversible tax (F23) -- this implement slice:**

18. Detect unmatched golden `def test_*`, wrap clean ones, copy/enable across same-family parts, Setup +Version / +Session (EPIC-A16) - **implemented**. A03 stays closed. No-code wizard stays parked.

**Next irreversible tax (F24) -- this implement slice:**

19. Campaign tags (`tags.yaml` + `TAGS.txt`) + chips/Tags page; STS-shaped rolling `sessions/report.json` + archive; auto-paste into `sheet_map` paste.photos; campaign golden workbook check/fix; AGENTS.md + UI contract (EPIC-A17) - **READY**.

**Separate verify wave (not this slice):** independent R-0003 on A07-A12. Do not reopen those epics to "check all tickets solve all".

**Parked:** A13 Excel merge-center / OneDrive / Excel MCP; A14 xyflow; cloud sync; mini-scope/CSV reconstruct; circuit drawing; drag-drop waves; no-code wizard (F23 detect/wrap is not the wizard); ML trainer; Comparator/Power bodies; dual-stack `main.py`; RS1G07 cpd/cin physics until clean wrap; Level full suites; DataLogger replace.

---

## 9. Feedback ledger

Append only. Never rewrite prior rows.

| # | Date | Raised in | Feedback | Routed to | Outcome |
|---|------|-----------|----------|-----------|---------|
| F1 | 2026-08-19 | founder session (F1) | Make this a **product** not just an OPA app. Left panel to switch different apps for different product types (Logic, OPA, later Level). Customisable to add new tests and new conditions. Other devices / new tests must have a slot. Prior improvements must be kept. | EPIC-A01 (boundary), EPIC-A02 (Logic wrap), EPIC-A03 (add-test slot), EPIC-A04 (conditions surface); Level full suite + wizard + Tauri + STM + delete legacy -> PARKED / out of scope | **Ack - this PRD.** Mode A authoring complete. Epic-agent next: slice **EPIC-A01** only. No tickets filed by prd-agent. |
| F2 | 2026-08-19 | epic-agent Mode A | Slice EPIC-A01 only into local ticket files (ponytail: 2 tickets; T03 invariants folded into T02). | EPIC-A01 | **Sliced.** Epic: `docs/epics/EPIC-A01-family-plugin-left-rail.md`. Tickets: A01-T01, A01-T02 under `docs/tickets/`. A02-A04 not sliced. No GitHub Issues. |
| F3 | 2026-08-19 | epic-agent Mode B | Re-derive EPIC-A01 acceptance from code + live RPC (not ticket checkboxes). | EPIC-A01 | **COMPLETE / closed-accepted.** Logic clears tests+fixtures; OpAmp restores 16 tests + G11/G_NEG100 catalog; START session-gated; category-first intact. Finding: `docs/subagents_findings/2026-08-19_epic-a01-mode-b-complete.md`. A02 not sliced here. |
| F4 | 2026-08-19 | epic-agent Mode A | Slice EPIC-A02 only (Logic wraps `logic_tests.py` into `ate/tests/logic` TestSpecs). | EPIC-A02 | **Sliced.** Epic: `docs/epics/EPIC-A02-logic-family-wrap.md`. Ticket: A02-T01 under `docs/tickets/`. Ponytail: 1 ticket (fixture honesty folded in). A03/A04 not sliced. No GitHub Issues. |
| F5 | 2026-09-03 | founder session (F5) | Continue building via PRD method; scalable for other products; check Logic and everything; soon more different products; **different timing** - plan carefully; prd/epic/ticket agents scale; plan execute /goal. | Interpreted both senses of timing. (1) **Roadmap timing** = later DUT families without rewriting runner -> maps to A03 (already in code; closed this intake). (2) **Measurement timing** = settle/timeout/pulse per product -> **irreversible next** -> amend EPIC-A04 (prefer amend over inventing A05). Full Level suite stays PARKED. Preserve OPA category-first, START gate, Logic wraps, no OPA G11 on Logic, Level stub, dual-stack parked, no GitHub Issues. | **Ack.** A03 closed-accepted from working tree (`docs/epics/EPIC-A03-add-test-slot.md`). A04 amended for per-family/per-test measurement timing. WIP this wave: **A04 only**. Recommended: spawn epic-agent **Mode A** to slice amended EPIC-A04 only. No tickets by prd-agent. No code. |
| F6 | 2026-09-03 | epic-agent Mode A | Slice amended EPIC-A04 only (per-family Run conditions + family-local measurement timing). Ponytail: 1 ticket. | EPIC-A04 | **Sliced.** Epic: `docs/epics/EPIC-A04-family-conditions-timing.md`. Ticket: A04-T01 under `docs/tickets/`. No TestSpec timing dataclass / wizard / A05. No GitHub Issues. No code. |
| F7 | 2026-09-03 | ticket-runner + R-0003 + Mode B UI | Implement A04-T01; adversary verify; live console click (Logic / OpAmp restore / Level stub). | EPIC-A04 | **COMPLETE / closed-accepted.** Finding: `docs/subagents_findings/2026-09-03_a04-t01-mode-b.md`. Next product lands via ingest + family-local timing; do not slice Level now. |
| F8 | 2026-09-03 | founder session (F8) | Not all features in console/report; **check all sync with test reports**; improve / check everything. Evidence: live xlsx test sheets vs OpAmp `lab_sheet` (Noise missing); `sheet_map` excel_sheet drift; paste only ORT+Settling; Slew/GBW screenshots not pasted; stubs RuntimeError; Logic out of wave. | **PRD amendment** -> **EPIC-A05** (new; A01-A04 stay closed). Maps to no open epic; founder authorized one next epic. | **Ack.** Appended. WIP: A05 only. Do not invent full Noise/PSRR suites. Do not reopen A01-A04. Do not slice Level. Recommended: spawn epic-agent **Mode A** on EPIC-A05 only. No tickets by prd-agent. No code. |
| F9 | 2026-09-03 | epic-agent Mode A | Slice EPIC-A05 only (sheet_map excel_sheet fix + Noise stub + runnable sync check). Ponytail: 1 ticket. Paste stretch out (Slew no anchors; GBW needs new place_*). | EPIC-A05 | **Sliced.** Epic: `docs/epics/EPIC-A05-lab-report-sync.md`. Ticket: A05-T01 under `docs/tickets/`. No Noise/PSRR suites / Level / wizard / A01-A04 reopen. No GitHub Issues. No code. |
| F10 | 2026-09-03 | ticket-runner + R-0003 Mode B | Implement A05-T01; adversary verify (pass + fail-path `Slew` + restore; family_load opamp=17; RPC noise). | EPIC-A05 | **COMPLETE / closed-accepted.** Finding: `docs/subagents_findings/2026-09-03_a05-t01-r0003-verify-pass.md`. Next product lands via ingest + family-local timing; do not invent A06 unless residual. |
| F11 | 2026-09-03 | founder session (F11) | Latest code is LabAutomation-1; ensure all used/correct tests become perfect workbook use cases. Two reports: DataLogger = pass-fail; ATE xlsx+sheet_map = characterization SoT. Keep ATE-native slew/settling/ORT/GBW. Wrap LA-1 SSR/LSR/NPR -> SSSR/LSSR/NPR. Optional GBW paste on A45. Park RS1G/Lim/PowerOn/Noise/PSRR. | **PRD amendment** -> **EPIC-A06** (new; A01-A05 stay closed). Maps to no open epic; founder authorized one next epic. Evidence finding: `docs/subagents_findings/2026-09-03_labautomation-1-scale.md`. | **Ack.** Appended. WIP: **A06 only**. Do not reopen A01-A05. Do not slice RS1G / Lim / Level / full PSRR. Do not replace DataLogger. Recommended: spawn epic-agent **Mode A** on EPIC-A06 only. No tickets by prd-agent. No code. |
| F12 | 2026-09-03 | epic-agent Mode A | Slice EPIC-A06 only (LA-1 BUFFER wraps SSSR/LSSR/NPR + screenshots + paste where sheet_map anchors exist; no hanging `input()`). Ponytail: 1 ticket. | EPIC-A06 | **Sliced.** Epic: `docs/epics/EPIC-A06-la1-buffer-wraps.md`. Ticket: A06-T01 under `docs/tickets/`. No PowerOn/Noise/PSRR / RS1G / Lim / Level / DataLogger replace / A01-A05 reopen. No GitHub Issues. No code. |
| F13 | 2026-09-03 | ticket-runner + R-0003 Mode B | Implement A06-T01; adversary verify (family_load + lab_report_sync; static no `input(`; place_sssr/lssr -> embed_photo; NPR no paste; stubs PowerOn/Noise/PSRR remain; RPC list_tests). | EPIC-A06 | **COMPLETE / closed-accepted.** Finding: `docs/subagents_findings/2026-09-03_a06-t01-r0003-verify-pass.md`. Next = remaining stubs PowerOn/Noise/PSRR parked - not A07 unless founder asks. |
| F14 | 2026-09-03 | founder session (F14) | Code must be modular Python; people must know where to change image layout; perfect waveform comparisons; graphs reconstructed on the website so they can visualize then adjust on the laptop; plan and execute; then continue build. | **PRD amendment** -> **EPIC-A07** (new; A01-A06 stay closed). Maps to no open epic; founder authorized next epic. | **Ack.** Appended. WIP: **A07 only**. Do not reopen A01-A06. Do not slice PowerOn / Noise / PSRR / RS1G / Lim. Do not replace DataLogger. Do not add a CSV chart library this wave. |
| F15 | 2026-09-03 | founder session (F15) | Platform easy for initial setup; DMM compatibility for those tests; add every single mapped test; ignore already-done steps; scale, continue build, verify everything. | **PRD amendment** -> **EPIC-A08**. A07 stays implemented (not reopened). | **Implemented** (R-0003 pending). Finding: `docs/subagents_findings/2026-09-03_a08-mapped-tests-dmm.md`. Map coverage 15/15. DMM optional at open; VOL needs DMM at run. |
| F16 | 2026-09-03 | founder session (F16) | All Logic tests + Soo/Lim different BTS; Ariff all have different specs/testing; everything manufacturable, editable, improvable; platform as a service more than software; team-tweakable. Chose Logic first, Lim next. | **PRD amendment** -> **EPIC-A09**. A07-A08 stay implemented (not reopened). Lim parked. | **Implemented** (R-0003 pending). Finding: `docs/subagents_findings/2026-09-03_a09-logic-campaign-platform.md`. RS29511=7 Soo; RS1G08=8 Ariff; map coverage family-aware. |
| F17 | 2026-09-03 | founder session (F17) | Lim RS2323 also need build; all open parts/components; check build and solve. RS0204 mentioned earlier but no source on disk. | **PRD amendment** -> **EPIC-A10**. A09 stays implemented. | **Ack.** Implemented (R-0003 pending). Finding: `docs/subagents_findings/2026-09-03_a10-lim-rs2323-open-inventory.md`. RS0204 parked. |
| F18 | 2026-09-03 | founder session (F18) | Implement RS0204 Standard_Lab_Report.xlsx into ATE; re-check LabAutomation-1 for author codes; if missing, founder will find him. | **PRD amendment** -> **EPIC-A11**. A10 stays implemented. | **Ack.** Workbook + datasheet on disk. No RS0204 Python in LA-1. Campaign + 16 honest missing-recipe TestSpecs. Do not wrap RS29511. |
| F20 | 2026-09-03 | founder session (F20) | RS2323 is analog switches; do not classify as Lim; other reports in Product Testing Report; operator login top-right; Lim codes in Downloads/code. | **PRD amendment.** Family = RUN-IC product class. Operator is a person filter/default. | **Ack.** Rail Analog SW. Owner picker. Lim's RS1G97/126 stay Logic. Do not import Downloads/code. |
| F21 | 2026-09-04 | founder session (F21) | Focus on codes into ATE first; Ariff latest introduces more tests; operators choose/deselect; Excel/xyflow later. | **PRD amendment** -> **EPIC-A12**. A01-A11 stay closed. Excel merge-center -> A13; xyflow -> A14. | **Ack.** Ariff Repo 16:41 is SoT for Logic DC/VOH/VOL. Native wraps in `ariff_dc.py`. No `import Ariff.*`. LDO not on RS1G. |
| F22 | 2026-09-08 | founder session (F22) | Ask mixed 8 products. Two forks: (1) campaign path INSERT operator folder BEFORE Version: `#Test_Database/{Component}/{Part}/{Package}/{Operator}/{Version_N}/` and migrate existing trees. (2) THIS SLICE core: category change must load a different suite; operator identity in folder + session; PSU/AWG safety hard rules -- OVP/OCP always ON, DUT-capped (interpret "set to the max" as protect always on, NOT DP832 30 V / 3 A; golden OVP=Vset+0.3 V, OCP=Iset+0.1 A, Iset default 100 mA). Park cloud sync, mini-scope/CSV reconstruct, circuit drawing, drag-drop waves, no-code wizard. Also "check all tickets solve all" -- A01-A06 closed-accepted; A07-A12 implemented R-0003 pending; do not reopen. | **PRD amendment** -> **EPIC-A15** (A13/A14 stay PARKED reserved). Maps to no open implement epic; founder authorized this slice. R-0003 A07-A12 = separate verify wave. | **Ack.** Tickets A15-T01 path+migrate, A15-T02 category suite, A15-T03 PSU/AWG protect. No GitHub Issues. No Comparator/Power bodies. |
| F23 | 2026-09-08 | founder session (F23) | Add-test / add-version / transferability: detect new `def test_*` from golden codebase + ate/tests; wrap into TestSpec; copy/enable onto another part; + buttons for Version / Session / Feature; standardised authoring; categorise. Chose first wave: detect+wrap+copy + +Version/+Session; scan both LA-1 and ate/tests; no in-browser editor. Pasted test_cpd/test_cin are detect examples (use input() -- must block). | **PRD amendment** -> **EPIC-A16**. A03 stays closed (slot exists). Full no-code wizard stays PARKED. A13/A14 stay PARKED. | **Implemented.** Tickets A16-T01/T02. `check_test_detect` OK. Worker restarted. Ctrl+F5 `?v=20260908f23`. |
| F24 | 2026-09-08 | founder session (F24) | New Tags page + chips beside model; multi tags (board rev / project); grep TAGS.txt; STS8200-style rolling session JSON + archive; auto-fill photos into sheet_map cells; golden format check/fix; AGENTS.md / UI contract for AI-safe edits. Separate branch from A16; A13 OneDrive/MCP stay parked. | **PRD amendment** -> **EPIC-A17**. A01-A16 stay closed. A13/A14 stay PARKED. | **Ack.** Tickets A17-T01 tags/datalog, A17-T02 Tags UI+contract, A17-T03 auto-paste+golden. Branch `epic/a17-tags-session-datalog`. No GitHub Issues. |

---

### EPIC-A17 - Tags, session datalog JSON, auto-paste, golden workbook

| Field | Value |
|-------|-------|
| Tier | capability (tags + datalog) + visible surface (Tags page) + paste honesty |
| Repo | this repo |
| Contract impact | additive RPCs; no breaking path change |
| Depends on | A15 operator path; A07 sheet_map paste SoT; A16 session JSON stays |
| Appetite | 1 wave (3 tickets) |
| Status | **READY** - 2026-09-08 F24. Epic file `docs/epics/EPIC-A17-tags-session-datalog.md` |

**One-liner:** Tags beside model + Tags page write `_manifest/tags.yaml` and grep-able `TAGS.txt`; each run updates rolling STS-shaped `sessions/report.json` (archive on end); session-end pastes screenshots into campaign xlsx via `paste.photos`; golden layout check/fix on campaign workbook; AGENTS.md + UI contract.

**Acceptance (testable):**
> WHEN the operator adds tags (board / project / free-text), THE SYSTEM SHALL persist `_manifest/tags.yaml` and campaign-root `TAGS.txt` and SHALL show chips beside Model. WHEN a run records steps, THE SYSTEM SHALL update `sessions/report.json` (STS header + sites + steps) and on end SHALL archive under `sessions/archive/`. WHEN a session ends and a test has real `paste.photos`, THE SYSTEM SHALL paste the latest DUT/channel image into the campaign workbook. WHEN `check_golden_workbook` runs, THE SYSTEM SHALL fail closed on golden-format drift; apply-then-recheck is the fix path. WHEN `check_ui_contract` runs, THE SYSTEM SHALL fail if a tab lacks its page section.

**Out of epic:** A13 OneDrive / Excel MCP; A14 xyflow; ML trainer; NTFS Keywords; reopen A01-A16.

---

## 10. Recommended next action

1. Implement **EPIC-A17** on branch `epic/a17-tags-session-datalog`. Ctrl+F5 console `?v=20260908f24`.
2. Separate wave: R-0003 verify on A07-A12 (do not reopen).
3. Keep A13/A14 and no-code wizard parked. RS1G07 CPD/CIN physics still parked until clean wraps exist.

**Model handoff:** implement Composer 2.5; validate/close Grok 4.5 high. Ports 8766 / 5174.
