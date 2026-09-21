# PRD-003 - Snippet pointer + trigger (original code stays SoT)

**Product:** PythonAutomation ATE (operator console + worker)
**Owner:** founder
**Status:** READY to slice. Mode A authoring complete. Do not implement in this document wave.
**Baseline:** [PRD-001](PRD-001-ate-multi-product-platform.md) A01-A21 stay closed or leftover-honest. [PRD-002](PRD-002-operator-profile-workflow.md) A22-A26 stay on their own board (A23 next there; A25/A26 must not fly with A27). Do **not** reopen A01-A21. Do **not** reopen A16 tickets as failed. A16 wrap-to-`imported_<id>.py` stays **leftover-honest**.
**Repos in scope:** this repo (`PythonAutomation` / origin `jian-hong/Python_Automation_JH`)
**Created:** 2026-09-15
**Updated:** 2026-09-15 (F1 founder: remember snippet location; UI scans/triggers; original code stays SoT)
**Epic home:** A27 at `docs/epics/EPIC-A27-snippet-pointer-trigger.md` (READY). Do **not** open GitHub Issues. Ticket files under `docs/tickets/`.
**Parked (inherited):** A13 OneDrive Excel MCP, A14 xyflow, no-code wizard, Monaco in-browser editor, ML trainer, delete `main.py`.

---

## 0. Nearness (this run)

**Artifact checked (files, not a live 5174 click this turn):**

1. Tests page `#page-detect` in `ate/ui/web/index.html` (~371): already says scan remembers `file:line` **and** still says "Wrap writes a scaffold". Mixed claim.
2. `ate/ui/web/app.js` `wrapSelectedDetected` (~4660): already logs `res.snippet` / `res.mode || "trigger"` and paints `list_tests` `t.source.file` (~3712). Button copy is "Remember + enable".
3. `ate/ui/web/UI_CONTRACT.md` item 14: already names pointer + trigger, `detected` + `located`.
4. Engine still A16 copy: `ate/core/test_detect.py` `wrap_detected_test` (~432-591) writes `ate/tests/<family>/imported_<id>.py` with a stub `run()` that does **not** call the original function. Return dict has `module`, not `snippet` / `mode`.
5. `list_detected_tests` (~348) returns unmatched `detected` only. No `located`. `scan_file` skips already-registered ids.
6. Worker `list_tests` (`ate/worker/server.py` ~237-296) already attaches `specs` from `load_part_specs` (`ate/core/specs.py` reads `ate/config/limits/<key>.yaml` then part yaml). **No `source` field.** Changing a limit in yaml already updates `list_tests.specs` without an `app.js` rewrite. A27 must not break that.
7. `ate/core/check_add_test.py` still requires wrap to write an imported scaffold. `ate/core/check_test_detect.py` still asserts `imported_detect_probe.py` is created.
8. `_blocked_reason` blocks `input()` (and helpers). It does **not** yet flag `Lim` / `Ariff` / `Soo` imports.
9. `ate/config/snippet_map.yaml` does **not** exist.

The live product is the operator console (`ate/` + worker **8766** + UI **5174**). This slice is closer when Detect **remembers** `file:lineno:fn` and Remember/START **runs that function**, not when the Tests page gains another wizard. A green invisible yaml with no Tests-page scan does not count as nearer. A painted "Remember" button that still writes `imported_*.py` is **not** shipped.

**Analog / TAS:** There is no TAS-ATE lane. This is **not** TAS-POINTER (computer-control HUD). The word pointer here means a `file:lineno:fn` map. Live surface: Tests `#page-detect` + Setup Test program. Frozen analog (LabAutomation-1 / vendor trees) is **scan source only**. Verdict: **extend-live**. SKIP a second clone. BAN n8n / grok-bot / AGPL / leaked trees / Monaco in-browser editor / executing vendor `Lim.*` / `Ariff.*` / `Soo.*` at wrap or scan time. Palantir P1 stays parked. Do not redesign left rail / fonts / UI_CONTRACT chrome.

---

## 1. Press release

### Remember where the test lives. Trigger it. Do not rewrite it.

**Subheading:** Characterization engineers keep editing the original `TestSpec`, part yaml, and limits yaml. The operator console scans those locations and START/Wrap fires the same function -- so a new test, a new parameter, or a changed threshold stays in sync without a second copy in the UI.

**Problem:** "Wrap copies a golden `def test_*` into `imported_<id>.py` and leaves a stub. We then fill a second body. If we keep building in the original file -- new tests, new parameters, new limits -- the copy diverges. I asked the console to remember the snippet where the code already is, not to become a no-code wizard that writes Python."

**Solution:** Detect AST-scans (never executes) and writes `ate/config/snippet_map.yaml` (`id -> file:lineno:fn`). Remember + enable on an AST-clean snippet registers a live trigger of that original function. Dirty snippets (`input()`, `Lim` / `Ariff` / `Soo` import) are remembered and blocked until Path B. UI never writes Python bodies. Params stay in `ate/config/parts/<key>.yaml`. Limits stay in `ate/config/limits/<key>.yaml`. Path B `register(TestSpec)` in `ate/tests/<family>/*.py` stays the realize path. Existing leftover `imported_input_off_leakage.py` stays this wave (honesty).

**Quote:** "I added `def test_foo` in the original file, scanned, and it showed up. I changed ICC max in limits yaml and Setup listed the new number. Wrap of a clean fixture did not create another `imported_*.py`. DEMO ran the original function." - characterization lead, internal (aspirational)

**Call to action:** Slice **EPIC-A27** only this wave. A16 tickets stay implemented. A13/A14 and the no-code wizard stay parked.

---

## 2. FAQ

### External

- **What is shipping in this slice?** Detect remembers snippet pointers. Remember + enable on a clean golden triggers the original function. Setup Test program can show `src file:line`. Limits/params keep loading from yaml. Scan sees a new `def test_*` on the next Detect.
- **Is this a no-code wizard?** No. PRD-001 parked wizard stays parked. Engineers still write Path B Python and yaml. The console does not author test bodies.
- **Does Wrap still write `imported_<id>.py`?** Not for new clean wraps after A27. A16 copy is leftover-honest. Do not delete `imported_input_off_leakage.py` this wave.
- **Will dirty goldens auto-run?** No. `input()` and vendor `Lim` / `Ariff` / `Soo` imports stay blocked. Remember them; do not live-trigger until Path B rewrite.
- **Do I edit tests in the browser?** No. Monaco / in-browser editor stays parked. Edit the original file in the repo (Cursor / vibe-code).
- **Does changing a limit require a UI change?** No. That already holds via `load_part_specs`. A27 must not start hardcoding specs in `app.js`.

### Internal

- **What could make this fail?** Treating Remember as another copy into `imported_*.py` (today's A16 leftover dressed as A27). Second: importing `Lim.*` at wrap/scan time because "trigger means execute the vendor tree". Third: putting test lists or min/max tables in `app.js`. Fourth: editing `runner.py` so START special-cases snippet ids. Fifth: calling this TAS-POINTER or unparking A14. Sixth: reopening A16 tickets as failed instead of leftover-honest.
- **What are we assuming?** (1) `TestSpec` + `register()` + `load_family` remain the runtime. (2) Scan stays AST-only (`ast.parse`, never `exec` / `import` of the golden during Detect). (3) Family load can rehydrate trigger specs from `snippet_map.yaml` without `runner.py`. (4) `list_tests.specs` already comes from limits yaml. (5) UI already consumes `snippet` / `located` / `source` -- the engine is behind the paint.
- **What would we have to be right about?** That "scale" means original files stay SoT (Path B py + parts yaml + limits yaml), and the console is an index + trigger, not a second author. If wrap keeps copying, every new parameter in the golden is a sync tax.
- **Why not reopen A16?** A16 shipped Detect + wrap-copy + Setup +. That copy is the leftover. Follow-on is pointer + trigger. Decomposition did not fail; the founder asked for the opposite of a wizard after seeing the copy diverge.
- **Why not A25?** A25 is suggest-enable of **existing registry ids** on this Version catalog. A27 changes wrap from copy to pointer. Shared files: `test_detect.py` + Tests page. Do not fly A25/A26 with A27. A25's line "Path C wrap remains a scaffold" is superseded by this PRD for the wrap action; suggest-enable stays A25.
- **GitHub Issues?** Still no unless the founder opts in.

---

## 3. Out of scope

Explicit park / refuse for this PRD:

- No-code test wizard (PRD-001 park stays park)
- In-browser Monaco / textarea that writes Python bodies
- A13 OneDrive Excel MCP / Graph / second Excel writer
- A14 xyflow / drag-drop canvas
- Users SQL table, login, Tags/Users path axis
- Copy-between-people; `btn-copy-tests`; wrap into another family
- Scraping en.run-ic.com into `#Test_Database`
- Rewriting `ate/core/runner.py`
- Rewriting `ate/core/database.py` path shape
- Live-import of vendor `Lim.*` / `Ariff.*` / `Soo.*` at scan or wrap time
- Deleting leftover `ate/tests/logic/imported_input_off_leakage.py` this wave
- Reopening A01-A21 or A16 tickets as failed
- Hardcoding test lists or spec tables in `app.js`
- TAS-POINTER HUD / UACC as the trigger mechanism
- n8n / second worker stack / executing goldens during Detect
- Folder delete, ML trainer, delete `main.py`

---

## 4. Success assertion

Testable from the operator / engineer seat:

> **WHEN** the operator runs Detect on the Tests page, **THE SYSTEM SHALL** AST-scan configured golden roots + `ate/tests` without executing those files, **SHALL** remember each `def test_*` as `file:lineno:fn` in `ate/config/snippet_map.yaml`, and **SHALL** list unmatched rows as `detected` and already-registered Path B / remembered rows as `located`.
>
> **WHEN** the operator Remember+enables an AST-clean snippet (no `input()`, no `Lim` / `Ariff` / `Soo` import), **THE SYSTEM SHALL** register a live trigger of that original function for START/DEMO, **SHALL NOT** write a new `imported_<id>.py`, and **SHALL NOT** rewrite the original file.
>
> **WHEN** the snippet is AST-dirty, **THE SYSTEM SHALL** still remember the pointer, **SHALL** mark it blocked, and **SHALL NOT** live-trigger until a Path B `register(TestSpec)` exists.
>
> **WHEN** START or DEMO runs that remembered clean id, **THE SYSTEM SHALL** call the original function (not an A16 stub that returns `imported scaffold -- fill body`).
>
> **WHEN** an engineer changes a spec in `ate/config/limits/<key>.yaml` (id match to `measurements[].id`), **THE SYSTEM SHALL** return the updated min/max on the next `list_tests.specs` without any UI rewrite.
>
> **WHEN** an engineer adds a new `def test_*` in the original file, **THE SYSTEM SHALL** show it on the next Detect scan.
>
> **WHEN** the UI lists tests, **THE SYSTEM SHALL** use registry + snippet map + part/limits yaml, and **SHALL NOT** hardcode the test list in `app.js`.

---

## 5. Code-verified baseline (do not rebuild)

Checked 2026-09-15 against the working tree:

| Area | State | Evidence |
|------|-------|----------|
| Detect scan | AST `def test_*`; unmatched only; `file` + `lineno` on rows | `test_detect.scan_file`; `list_detected_tests` |
| Wrap | **writes** `imported_<id>.py` stub; does not call original | `wrap_detected_test`; return `module` |
| UI paint | ahead of engine (Remember, `located`, `snippet`, `source`) | `app.js`; `UI_CONTRACT.md` item 14; `index.html` mixed hint |
| Path B SoT | `register(TestSpec)` in `ate/tests/<family>/` | `AGENTS.md`; `docs/VIBE_CODE.md`; `eugene_cap.py` |
| Params SoT | `ate/config/parts/<key>.yaml` `enabled_tests` | AGENTS.md Where-to-change |
| Limits SoT | `ate/config/limits/<key>.yaml` then part yaml | `specs.load_part_specs`; worker `list_tests` `specs` |
| Catalog Path A | this Version `_manifest/test_catalog.yaml` | Tests page Save |
| A16 leftover | `imported_input_off_leakage.py` still a fill-body scaffold | `check_add_test` requires the marker |
| AST block | `input()` + helpers; not vendor imports yet | `_blocked_reason` |
| Snippet map | missing | no `snippet_map.yaml` |
| `runner.py` | family via `load_family`; do not add tests here | `check_add_test` |
| Specs without UI rewrite | **already holds** | `load_part_specs` + `list_tests` |

False premises refused: the UI is not the SoT today (it already tries to paint pointers). `list_tests.specs` is not a new feature. Detect does not yet persist a map. Wrap does not yet trigger.

---

## 6. Model / dispatch law (this wave)

| Role | Model |
|------|-------|
| prd-agent / epic-agent / verify | Grok 4.5 or Grok 4.6 |
| implement | Composer 2.5 |
| ticket-runner default | Composer 2.5 unless founder overrides |

**WIP:** at most two epics in flight; at least one human-inspectable. A27 Tests page is inspectable. **Do not pair A27 with A25 or A26** -- all three own `test_detect.py` and/or Tests `#page-detect`. A23 Forget (Settings) does not share those files; PRD-002 may still seat A23 in parallel if a second writer exists. Do not seat A27 with another wrap/catalog ticket.

**F-0009:** one writer per working tree. No GitHub Issues.

---

## 7. Epic sketches (irreversibility order)

Epics are sketches here. Ticket files are Mode A under `docs/tickets/`. Appetite: one focused agent wave. Do not reopen A01-A21 or A16 tickets.

Ordering law: irreversibility, not value. Schema + AST gate before wrap-trigger before UI honesty.

### EPIC-A27 - Remember snippet pointers and trigger the original function

| Field | Value |
|-------|-------|
| Tier | foundation (`snippet_map.yaml`) + boundary (AST gate, no vendor import) + capability (live trigger) + visible Tests surface |
| Repo | this repo |
| Contract impact | additive (`snippet_map.yaml`; wrap RPC grows `snippet` / `mode`; `list_detected_tests` grows `located`; `list_tests` grows `source`). Wrap **stops writing** new `imported_*.py` (A16 leftover replaced, not a broken campaign path). |
| Depends on | A16 implemented leftover (Detect RPC + Tests page exist). A03 Path B slot closed. |
| Blocks | A25/A26 while in flight (shared Tests page + `test_detect.py`) |
| Appetite | 1 wave (3 tickets, sequential) |
| Status | **READY** |
| File | `docs/epics/EPIC-A27-snippet-pointer-trigger.md` |

**Buyer-visible outcome:** Detect lists snippet rows with file:line (unmatched and located). Remember on a clean fixture does not create `imported_*.py`. DEMO/START of that id runs the original function. Change a limit in limits yaml; Setup Test program specs update. Add `def test_*` in the original file; next scan sees it.

**Acceptance:** see section 4 (buyer seat). Ticket-level WHENs live in A27-T01/T02/T03.

**Design constraints (for tickets, not pre-solved here):**

- Persist `id -> {file, lineno, fn, family, ast_clean, blocked_reason}` in `ate/config/snippet_map.yaml`.
- Scan = AST only. Never `exec` / import the golden during Detect.
- File-level `Lim` / `Ariff` / `Soo` import (and `input()`) => blocked remember, no live trigger.
- Rehydrate trigger `TestSpec`s on `load_family` from the map (hook in `test_detect` / `registry.load_family`). **Do not edit `runner.py`.**
- One shared trigger helper that importlib-loads the remembered path and calls `fn` only if still AST-clean. Do not generate a new per-id `.py`.
- Path B modules already in the registry stay SoT; the map records their pointer; START still uses `register()`.
- Params/limits stay yaml. UI reads `list_tests`; it does not write Python or spec tables.
- Leftover `imported_input_off_leakage.py` stays on disk this wave.
- Invert `check_test_detect` / `check_add_test` wrap-copy asserts when T02 lands.
- Human-inspectable: founder can open Tests -> Detect, see file:line, Remember a clean fixture, and not find a new `imported_*.py`.

**Out of epic:** no-code wizard; Monaco; A13/A14; Users table; copy-between-people; scrape; `runner.py`; vendor live-import; delete leftover scaffold; A23-A26 implement; reopen A16 tickets.

---

## 8. File contention (named so writers do not collide)

| File | Owner epic | Do not also edit in |
|------|------------|---------------------|
| `ate/config/snippet_map.yaml` | A27 | nobody else |
| `ate/core/test_detect.py` | A27 T01 then T02 | A25 / A26 while A27 in flight |
| `ate/core/registry.py` `load_family` rehydrate hook only | A27-T02 | do not retouch FAMILY_PACKAGES |
| `ate/core/check_test_detect.py` / `check_add_test.py` | A27 T01 then T02 | A25 |
| `ate/worker/server.py` wrap pass-through + `list_tests.source` | A27-T02 then T03 | additive only |
| `ate/ui/web/app.js` + `index.html` Tests detect | A27-T03 | A25 / A26 |
| `ate/core/runner.py` | **nobody** | all of A27 |
| `ate/core/database.py` `DbContext.root()` | **nobody** | all of A27 |
| leftover `imported_input_off_leakage.py` | **nobody this wave** | do not delete |

Wire (T01 map + T02 wrap RPC) then consumer (T03 `list_tests.source` + hint). Do not implement T03 in the same agent run as T01. UI already consumes `snippet` / `located`; T02 must return those fields so the paint stops lying.

---

## 9. Feedback ledger

Append only. Never rewrite prior rows.

| # | Date | Raised in | Feedback | Routed to | Outcome |
|---|------|-----------|----------|-----------|---------|
| F1 | 2026-09-15 | founder session (PRD-003) | If in the future, the code just remembers the snippet section where it is located. The UI does NOT rewrite the code. It just triggers the code section / scans the code section. So if they continue to build and scale, or change parameters in the original code location (how they code), or they add new code like a new test, new parameters, change limit, change threshold -- everything stays in sync without needing to change a lot. | **This PRD.** Opposite of no-code wizard. A16 copy leftover-honest. Original SoT: Path B py, parts yaml, limits yaml, golden `file:lineno:fn` in `snippet_map.yaml`. Live-trigger only if AST-clean. UI scans/triggers by id. No `runner.py` / `database.py` path edit. | **Ack.** WIP: **A27 only**. Mode A tickets A27-T01/T02/T03. No product code this sitting. A13/A14 / wizard parked. A16 tickets not reopened. |

---

## 10. Recommended next action

1. Implement Composer 2.5 on **A27-T01** then T02 then T03 after this Mode A.
2. Independent verify (different run) Grok 4.5 or 4.6 against section 4.
3. Do not start A25/A26 in the same sitting. Keep A13/A14 and the wizard parked.
4. Do not delete `imported_input_off_leakage.py` this wave.

**Ports:** 8766 / 5174. Idle-restart worker after T01/T02. Ctrl+F5 after T03.
